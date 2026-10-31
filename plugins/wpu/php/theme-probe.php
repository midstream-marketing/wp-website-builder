<?php
/**
 * Read-only: how does the active theme build its header/footer, and will Elementor Pro theme-builder
 * templates take over? Reports theme supports, nav-menu locations, Elementor location registration,
 * theme-specific post types (header/footer builders), the theme's own options, and any Elementor
 * library documents already on the site.
 *   powershell -File bin/rwpphp.ps1 php/theme-probe.php
 */
defined( 'ABSPATH' ) || exit;

$theme = wp_get_theme();
printf( "theme: %s %s (template %s)%s\n", $theme->get( 'Name' ), $theme->get( 'Version' ), $theme->get_template(), $theme->parent() ? ' child of ' . $theme->parent()->get( 'Name' ) : '' );
printf( "author: %s | uri: %s\n", $theme->get( 'Author' ), $theme->get( 'ThemeURI' ) );

echo "\n[theme supports]\n  ";
$sup = array();
foreach ( array( 'woocommerce', 'wc-product-gallery-zoom', 'wc-product-gallery-lightbox', 'wc-product-gallery-slider', 'custom-logo', 'title-tag', 'elementor', 'header-footer-elementor' ) as $f ) {
	$sup[] = $f . '=' . ( current_theme_supports( $f ) ? 'yes' : 'no' );
}
echo implode( '  ', $sup ) . "\n";

echo "\n[nav menu locations]\n";
foreach ( get_registered_nav_menus() as $loc => $label ) {
	printf( "  %-18s %s\n", $loc, $label );
}

echo "\n[elementor pro theme locations]\n";
if ( class_exists( '\ElementorPro\Modules\ThemeBuilder\Module' ) ) {
	$lm = \ElementorPro\Modules\ThemeBuilder\Module::instance()->get_locations_manager();
	foreach ( (array) $lm->get_locations() as $k => $l ) {
		printf( "  %-20s %s\n", $k, ! empty( $l['is_core'] ) ? '(core)' : '(registered by theme/plugin)' );
	}
	printf( "  header location used by theme: %s\n", has_action( 'elementor/theme/register_locations' ) ? 'a theme/plugin hooks register_locations' : 'no hook found' );
} else {
	echo "  Elementor Pro theme builder not loaded\n";
}

echo "\n[theme-specific post types]\n";
foreach ( get_post_types( array( '_builtin' => false ), 'objects' ) as $pt ) {
	if ( in_array( $pt->name, array( 'product', 'product_variation', 'shop_order', 'shop_coupon', 'shop_order_refund', 'elementor_library', 'e-landing-page', 'elementor_font', 'elementor_icons', 'elementor_snippet' ), true ) ) {
		continue;
	}
	$n = (int) wp_count_posts( $pt->name )->publish;
	printf( "  %-26s %-30s %d published\n", $pt->name, $pt->label, $n );
}

echo "\n[elementor library documents]\n";
foreach ( get_posts( array( 'post_type' => 'elementor_library', 'posts_per_page' => 50, 'post_status' => 'any' ) ) as $p ) {
	printf( "  #%-6d %-10s %-34s type=%-12s conditions=%s\n", $p->ID, $p->post_status, substr( $p->post_title, 0, 34 ), get_post_meta( $p->ID, '_elementor_template_type', true ), wp_json_encode( get_post_meta( $p->ID, '_elementor_conditions', true ) ) );
}

echo "\n[theme files that mention header/footer builders]\n";
$dir = get_template_directory();
$it  = new RecursiveIteratorIterator( new RecursiveDirectoryIterator( $dir, FilesystemIterator::SKIP_DOTS ) );
$hits = array();
foreach ( $it as $f ) {
	if ( 'php' !== strtolower( $f->getExtension() ) || $f->getSize() > 400000 ) {
		continue;
	}
	$c = (string) file_get_contents( $f->getPathname() );
	foreach ( array( 'register_location', 'elementor_theme_do_location', "register_post_type( 'mixxcazt", 'header_builder', 'footer_builder', 'get_header_layout', 'mixxcazt_header', 'mixxcazt_footer' ) as $needle ) {
		if ( false !== stripos( $c, $needle ) ) {
			$hits[ str_replace( $dir, '', $f->getPathname() ) ][] = $needle;
		}
	}
}
foreach ( array_slice( $hits, 0, 25, true ) as $file => $n ) {
	printf( "  %-58s %s\n", $file, implode( ', ', array_unique( $n ) ) );
}

echo "\n[theme options / customizer mods]\n";
$mods = (array) get_theme_mods();
printf( "  %d theme mods: %s\n", count( $mods ), implode( ', ', array_slice( array_keys( $mods ), 0, 30 ) ) );
foreach ( wp_load_alloptions() as $k => $v ) {
	if ( false !== stripos( $k, 'mixxcazt' ) ) {
		printf( "  option %-40s %s\n", $k, substr( (string) $v, 0, 100 ) );
	}
}
