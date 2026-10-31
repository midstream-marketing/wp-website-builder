<?php
/**
 * Apply ONE group of speed settings, with the previous values printed for rollback.
 * Measure before and after every group (python tools/perf/psi.py); keep a group only
 * if mobile LCP/CLS/TBT did not get worse.
 *
 *   powershell -File scripts/rwpphp.ps1 php/speed-apply.php group=elementor           dry run
 *   powershell -File scripts/rwpphp.ps1 php/speed-apply.php group=elementor apply     make it
 *   powershell -File scripts/rwpphp.ps1 php/speed-apply.php restore_b64=<...> apply   put the "before" values back
 *
 * Groups:
 *   elementor  - Elementor's performance experiments + optimised loading options
 *   fonts      - serve Google Fonts locally, font-display: swap
 *   lazybg     - lazy-load Elementor background images
 *   cssfile    - CSS print method = external file (use "cssinline" on hosts whose
 *                cleanup deletes uploads/elementor/css - see knowledge/GOTCHAS.md)
 *   cssinline  - CSS print method = internal embedding
 *   transients - delete expired transients (database tidy; nothing visible changes)
 *
 * Deliberately NOT here: anything a caching plugin owns (configure the one the host
 * already has, in its own settings), delaying third-party scripts (tracking may break -
 * ask first), and wp-config.php constants (not writable from here on most hosts).
 *
 * The output ends with a line   BEFORE_JSON {...}   - the wrapper saves it as the rollback.
 */
defined( 'ABSPATH' ) || exit;

$args    = (array) ( $argv ?? array() );
$apply   = in_array( 'apply', $args, true );
$group   = '';
$restore = null;
foreach ( $args as $a ) {
	if ( 0 === strpos( (string) $a, 'group=' ) ) {
		$group = sanitize_key( substr( (string) $a, 6 ) );
	}
	if ( 0 === strpos( (string) $a, 'restore_b64=' ) ) {
		$restore = json_decode( (string) base64_decode( substr( (string) $a, 12 ), true ), true );
	}
}

$experiments = array(
	'e_optimized_assets_loading',   // Improved Asset Loading
	'e_optimized_css_loading',      // Improved CSS Loading
	'e_font_icon_svg',              // Inline Font Icons (Pro "fal/far" icon names cannot inline - check icons after)
	'e_dom_optimization',           // Optimized DOM Output (older Elementor)
	'additional_custom_breakpoints',
	'container',                    // Flexbox Container - new layouts only; existing sections are untouched
);

$groups = array(
	'elementor'  => array_merge(
		array_fill_keys( array_map( function ( $e ) { return 'elementor_experiment-' . $e; }, $experiments ), 'active' ),
		array( 'elementor_optimized_image_loading' => '1', 'elementor_optimized_gutenberg_loading' => '1', 'elementor_load_fa4_shim' => '' )
	),
	'fonts'      => array( 'elementor_local_google_fonts' => '1', 'elementor_font_display' => 'swap' ),
	'lazybg'     => array( 'elementor_lazy_load_background_images' => '1' ),
	'cssfile'    => array( 'elementor_css_print_method' => 'external' ),
	'cssinline'  => array( 'elementor_css_print_method' => 'internal' ),
);

if ( is_array( $restore ) ) {
	$want = $restore;
	echo "RESTORE previous values\n";
} elseif ( 'transients' === $group ) {
	global $wpdb;
	$expired = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$wpdb->options} WHERE option_name LIKE %s AND option_value < %d", $wpdb->esc_like( '_transient_timeout_' ) . '%', time() ) );
	printf( "expired transients: %d\n", $expired );
	if ( $apply ) {
		delete_expired_transients( true );
		echo "deleted.\n";
	} else {
		echo "(dry run - add 'apply')\n";
	}
	echo "BEFORE_JSON {}\n";
	return;
} elseif ( isset( $groups[ $group ] ) ) {
	$want = $groups[ $group ];
	if ( 'elementor' === $group && defined( 'ELEMENTOR_VERSION' ) ) {
		printf( "Elementor %s%s\n", ELEMENTOR_VERSION, defined( 'ELEMENTOR_PRO_VERSION' ) ? ' / Pro ' . ELEMENTOR_PRO_VERSION : '' );
	}
} else {
	exit( "group= must be one of: " . implode( ', ', array_merge( array_keys( $groups ), array( 'transients' ) ) ) . "\n" );
}

if ( ! defined( 'ELEMENTOR_VERSION' ) && ! is_array( $restore ) ) {
	exit( "Elementor is not active - nothing in this group applies.\n" );
}

$before  = array();
$changes = 0;
foreach ( $want as $opt => $val ) {
	$cur = get_option( $opt, null );
	$before[ $opt ] = $cur;
	// null means "option absent": it only matches another null, never "".
	$same = ( null === $cur && null === $val ) || ( null !== $cur && null !== $val && (string) $cur === (string) $val );
	printf( "  %s %-48s %s%s\n", $same ? '=' : '~', $opt, wp_json_encode( $cur ), $same ? '' : ' -> ' . wp_json_encode( $val ) );
	if ( $same ) {
		continue;
	}
	$changes++;
	if ( $apply ) {
		if ( null === $val ) {
			delete_option( $opt );
		} else {
			update_option( $opt, $val );
		}
	}
}

if ( $apply && $changes && class_exists( '\Elementor\Plugin' ) ) {
	// New settings only reach visitors once the generated CSS is rebuilt.
	\Elementor\Plugin::$instance->files_manager->clear_cache();
	do_action( 'litespeed_purge_all' );
	if ( function_exists( 'rocket_clean_domain' ) ) {
		rocket_clean_domain();
	}
	echo "Elementor CSS regenerated; page caches purged where a known cache plugin is active.\n";
}

printf( "\n%d change(s).%s\n", $changes, $apply ? ' APPLIED.' : " (dry run - add 'apply')" );
echo 'BEFORE_JSON ' . wp_json_encode( $before ) . "\n";
