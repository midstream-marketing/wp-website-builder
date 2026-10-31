<?php
/**
 * Elementor Pro theme-builder conditions: what each template's post meta says
 * versus the cached option Elementor Pro actually reads when rendering.
 * Dry run shows the difference; 'apply' regenerates the cache.
 *
 *   powershell -File bin/rwpphp.ps1 php/conditions.php          # read-only
 *   powershell -File bin/rwpphp.ps1 php/conditions.php apply    # rebuild cache
 */

defined( 'ABSPATH' ) || exit;

$apply = in_array( 'apply', $argv ?? array(), true );

echo "Elementor Pro: " . ( defined( 'ELEMENTOR_PRO_VERSION' ) ? ELEMENTOR_PRO_VERSION : 'NOT LOADED' ) . "\n";
echo "Pro licence active: " . ( class_exists( '\ElementorPro\License\API' ) && \ElementorPro\License\API::is_license_active() ? 'yes' : 'no / unknown' ) . "\n\n";

echo "Template meta (_elementor_conditions):\n";
foreach ( get_posts( array( 'post_type' => 'elementor_library', 'post_status' => 'any', 'numberposts' => -1 ) ) as $t ) {
	$type = get_post_meta( $t->ID, '_elementor_template_type', true );
	if ( ! in_array( $type, array( 'header', 'footer', 'single', 'single-page', 'archive', 'error-404' ), true ) ) {
		continue;
	}
	printf( "  #%-5d %-8s %-8s %-20s %s\n", $t->ID, $t->post_status, $type, $t->post_title, wp_json_encode( get_post_meta( $t->ID, '_elementor_conditions', true ) ) );
}

echo "\nCached option elementor_pro_theme_builder_conditions:\n";
echo '  ' . wp_json_encode( get_option( 'elementor_pro_theme_builder_conditions', '(missing)' ) ) . "\n";

echo "\nHello theme header/footer switches:\n";
foreach ( array( 'hello_elementor_settings_header_footer', 'hello_elementor_settings_hello_header_footer' ) as $o ) {
	printf( "  %-46s %s\n", $o, wp_json_encode( get_option( $o, '(unset)' ) ) );
}

if ( class_exists( '\ElementorPro\Modules\ThemeBuilder\Module' ) ) {
	$cache = \ElementorPro\Modules\ThemeBuilder\Module::instance()->get_conditions_manager()->get_cache();
	if ( $apply ) {
		$cache->regenerate();
		echo "\nAPPLIED: conditions cache regenerated.\n";
		echo '  now: ' . wp_json_encode( get_option( 'elementor_pro_theme_builder_conditions' ) ) . "\n";
	} else {
		echo "\n(dry run - add 'apply' to regenerate the conditions cache)\n";
	}
} else {
	echo "\nElementor Pro theme builder module not available.\n";
}
