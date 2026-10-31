<?php
/**
 * Environment snapshot. Run this first on any site you have not seen before.
 *
 *   pwsh bin/wpphp.ps1 php/site-info.php
 */

defined( 'ABSPATH' ) || exit;

function wpsb_h( string $title ): void {
	echo "\n" . str_repeat( '=', 74 ) . "\n  " . strtoupper( $title ) . "\n" . str_repeat( '=', 74 ) . "\n";
}

wpsb_h( 'core' );
printf( "%-24s %s\n", 'WordPress', get_bloginfo( 'version' ) );
printf( "%-24s %s\n", 'PHP', PHP_VERSION );
printf( "%-24s %s\n", 'Site URL', get_option( 'siteurl' ) );
printf( "%-24s %s\n", 'Home', get_option( 'home' ) );
printf( "%-24s %s\n", 'Permalinks', get_option( 'permalink_structure' ) ?: '(plain — often the cause of 404s)' );
printf( "%-24s %s\n", 'Search engines', get_option( 'blog_public' ) ? 'allowed' : 'DISCOURAGED (noindex is on)' );
printf( "%-24s %s\n", 'WP_DEBUG', defined( 'WP_DEBUG' ) && WP_DEBUG ? 'on' : 'off' );

wpsb_h( 'theme' );
$theme = wp_get_theme();
printf( "%-24s %s %s\n", 'Active', $theme->get( 'Name' ), $theme->get( 'Version' ) );

if ( $theme->parent() ) {
	printf( "%-24s %s\n", 'Parent', $theme->parent()->get( 'Name' ) );
}

foreach ( wp_get_themes() as $slug => $t ) {
	$missing = $t->get( 'Template' ) && ! wp_get_theme( $t->get( 'Template' ) )->exists();
	if ( $missing ) {
		printf( "  BROKEN: %s needs missing parent '%s'\n", $t->get( 'Name' ), $t->get( 'Template' ) );
	}
}

wpsb_h( 'plugins' );
require_once ABSPATH . 'wp-admin/includes/plugin.php';
$active = (array) get_option( 'active_plugins', array() );

foreach ( get_plugins() as $file => $p ) {
	printf(
		"  %-9s %-38s %s\n",
		in_array( $file, $active, true ) ? 'active' : 'inactive',
		substr( $p['Name'], 0, 38 ),
		$p['Version']
	);
}

wpsb_h( 'pages' );
foreach ( get_posts(
	array(
		'post_type'      => 'page',
		'post_status'    => array( 'publish', 'draft', 'private' ),
		'posts_per_page' => -1,
		'orderby'        => 'title',
		'order'          => 'ASC',
	)
) as $p ) {
	$builder = 'builder' === get_post_meta( $p->ID, '_elementor_edit_mode', true ) ? 'elementor' : '';
	printf(
		"  %-6d %-9s %-34s /%s/%s  %s\n",
		$p->ID,
		$p->post_status,
		substr( $p->post_title, 0, 34 ),
		$p->post_name,
		str_repeat( ' ', max( 0, 22 - strlen( $p->post_name ) ) ),
		$builder ?: ( strlen( $p->post_content ) < 60 ? 'THIN (' . strlen( $p->post_content ) . ' chars)' : '' )
	);
}

wpsb_h( 'menus' );
foreach ( get_registered_nav_menus() as $loc => $label ) {
	$menus = get_nav_menu_locations();
	$id    = $menus[ $loc ] ?? 0;
	$obj   = $id ? wp_get_nav_menu_object( $id ) : null;
	printf( "  %-22s %s\n", $loc, $obj ? $obj->name . ' (' . $obj->count . ' items)' : '— NOT ASSIGNED —' );
}

if ( class_exists( 'WooCommerce' ) ) {
	wpsb_h( 'woocommerce' );
	printf( "%-24s %s\n", 'Version', WC()->version );
	printf( "%-24s %s\n", 'Currency', get_option( 'woocommerce_currency' ) );
	printf( "%-24s %s\n", 'Selling to', get_option( 'woocommerce_allowed_countries' ) );
	printf( "%-24s %s\n", 'Products', wp_count_posts( 'product' )->publish );

	$gateways = WC()->payment_gateways() ? WC()->payment_gateways->get_available_payment_gateways() : array();
	printf( "%-24s %s\n", 'Payment gateways', $gateways ? implode( ', ', wp_list_pluck( $gateways, 'title' ) ) : '*** NONE — CHECKOUT CANNOT COMPLETE ***' );

	foreach ( array( 'shop', 'cart', 'checkout', 'myaccount' ) as $page ) {
		$id = wc_get_page_id( $page );
		printf( "  %-12s %s\n", $page, $id > 0 ? get_permalink( $id ) : '*** NOT SET ***' );
	}

	$zones = WC_Shipping_Zones::get_zones();
	echo "  shipping zones:\n";
	foreach ( $zones as $z ) {
		$zone = WC_Shipping_Zones::get_zone( (int) $z['zone_id'] );
		printf( "    %-22s %s\n", $zone->get_zone_name(), implode( ', ', wp_list_pluck( $zone->get_shipping_methods( true ), 'id' ) ) ?: '(no enabled methods)' );
	}
}

wpsb_h( 'recent fatal errors' );
$logs = glob( WP_CONTENT_DIR . '/uploads/wc-logs/fatal-errors-*.log' );
$logs = $logs ?: array();

if ( file_exists( WP_CONTENT_DIR . '/debug.log' ) ) {
	$logs[] = WP_CONTENT_DIR . '/debug.log';
}

if ( ! $logs ) {
	echo "  no log files found\n";
} else {
	foreach ( $logs as $log ) {
		printf( "  %s  (modified %s)\n", basename( $log ), gmdate( 'Y-m-d H:i', filemtime( $log ) ) );
		$lines = array_slice( array_filter( explode( "\n", (string) file_get_contents( $log ) ) ), -3 );
		foreach ( $lines as $l ) {
			echo '      ' . substr( trim( $l ), 0, 150 ) . "\n";
		}
	}
	echo "\n  Check the timestamps — most entries are stale.\n";
}

echo "\n";
