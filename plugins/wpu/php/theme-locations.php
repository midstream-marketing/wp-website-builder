<?php
/**
 * Read-only: can Elementor Pro's theme builder replace this theme's header and
 * footer? Lists registered theme-builder locations, whether the active theme
 * hooks them, existing header/footer templates, and where the logo lives
 * (custom_logo, theme-option frameworks, logo-like attachments).
 *
 *   powershell -File bin/rwpphp.ps1 php/theme-locations.php
 */

defined( 'ABSPATH' ) || exit;

$theme = wp_get_theme();
printf( "theme: %s %s (parent: %s)\n", $theme->get( 'Name' ), $theme->get( 'Version' ), $theme->parent() ? $theme->parent()->get( 'Name' ) : '-' );

if ( class_exists( '\ElementorPro\Modules\ThemeBuilder\Module' ) ) {
	$lm   = \ElementorPro\Modules\ThemeBuilder\Module::instance()->get_locations_manager();
	$locs = $lm->get_locations();
	echo "\nregistered theme-builder locations:\n";
	foreach ( $locs as $name => $args ) {
		printf( "  %-10s label=%-10s edit_in_content=%s\n", $name, $args['label'] ?? '', wp_json_encode( $args['edit_in_content'] ?? null ) );
	}
	// Did the theme register core locations itself, or does Elementor Pro fall back to its own hooks?
	printf( "\ntheme calls elementor_theme_do_location(): %s\n",
		( function () {
			foreach ( array( get_template_directory(), get_stylesheet_directory() ) as $dir ) {
				foreach ( array( 'header.php', 'footer.php' ) as $f ) {
					$p = $dir . '/' . $f;
					if ( is_readable( $p ) && strpos( (string) file_get_contents( $p ), 'elementor_theme_do_location' ) !== false ) {
						return "yes ($f in " . basename( $dir ) . ')';
					}
				}
			}
			return 'no (Elementor Pro replaces header.php/footer.php via its own get_header/get_footer hooks)';
		} )() );
}
printf( "hooked 'elementor/theme/register_locations': %s\n", has_action( 'elementor/theme/register_locations' ) ? 'yes' : 'no' );

echo "\nexisting header/footer templates:\n";
foreach ( get_posts( array( 'post_type' => 'elementor_library', 'post_status' => 'any', 'numberposts' => -1, 'meta_query' => array( array( 'key' => '_elementor_template_type', 'value' => array( 'header', 'footer', 'single-page', 'error-404' ), 'compare' => 'IN' ) ) ) ) as $t ) {
	printf( "  #%-5d %-8s %-8s %s conditions=%s\n", $t->ID, $t->post_status, get_post_meta( $t->ID, '_elementor_template_type', true ), $t->post_title, wp_json_encode( get_post_meta( $t->ID, '_elementor_conditions', true ) ) );
}
echo 'conditions cache: ' . wp_json_encode( get_option( 'elementor_pro_theme_builder_conditions' ) ) . "\n";

echo "\nlogo:\n";
$cl = (int) get_theme_mod( 'custom_logo' );
printf( "  custom_logo theme mod: %s\n", $cl ? "#$cl " . wp_get_attachment_url( $cl ) : '(none)' );
foreach ( array( 'doctio_options', 'doctio', '_doctio_options', 'themedraft_options' ) as $opt ) {
	$v = get_option( $opt );
	if ( $v ) {
		$json = wp_json_encode( $v );
		preg_match_all( '/"([a-z_]*logo[a-z_]*)":(\{[^{}]*\}|"[^"]*")/i', $json, $m, PREG_SET_ORDER );
		foreach ( array_slice( $m, 0, 8 ) as $x ) {
			printf( "  %s.%s = %s\n", $opt, $x[1], mb_strimwidth( stripslashes( $x[2] ), 0, 140, '…' ) );
		}
	}
}
foreach ( get_posts( array( 'post_type' => 'attachment', 'numberposts' => 12, 's' => 'logo' ) ) as $a ) {
	$meta = wp_get_attachment_metadata( $a->ID );
	printf( "  attachment #%-5d %-40s %sx%s %s\n", $a->ID, mb_strimwidth( $a->post_title, 0, 40 ), $meta['width'] ?? '?', $meta['height'] ?? '?', wp_get_attachment_url( $a->ID ) );
}
foreach ( get_posts( array( 'post_type' => 'attachment', 'numberposts' => 12, 's' => 'nexxus' ) ) as $a ) {
	$meta = wp_get_attachment_metadata( $a->ID );
	printf( "  attachment #%-5d %-40s %sx%s %s\n", $a->ID, mb_strimwidth( $a->post_title, 0, 40 ), $meta['width'] ?? '?', $meta['height'] ?? '?', wp_get_attachment_url( $a->ID ) );
}
