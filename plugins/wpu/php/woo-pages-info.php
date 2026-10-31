<?php
/**
 * Read-only: how the WooCommerce cart / checkout / my-account pages are built
 * (blocks vs shortcode vs Elementor), their template, and relevant Woo settings.
 *
 *   powershell -File bin/rwpphp.ps1 php/woo-pages-info.php
 */

defined( 'ABSPATH' ) || exit;

foreach ( array( 'cart', 'checkout', 'myaccount' ) as $k ) {
	$id = (int) get_option( "woocommerce_{$k}_page_id" );
	$p  = get_post( $id );
	if ( ! $p ) {
		printf( "%-9s: (no page)\n", $k );
		continue;
	}
	$el = (string) get_post_meta( $id, '_elementor_data', true );
	printf( "%-9s: #%d /%s/ %s template=%s elementor=%s (%d bytes)\n", $k, $id, $p->post_name, $p->post_status, get_post_meta( $id, '_wp_page_template', true ) ?: 'default', get_post_meta( $id, '_elementor_edit_mode', true ) ?: 'no', strlen( $el ) );
	printf( "           content: %s\n", mb_strimwidth( preg_replace( '/\s+/', ' ', $p->post_content ), 0, 300, '…' ) );
	if ( $el ) {
		preg_match_all( '/"widgetType":"([^"]+)"/', $el, $m );
		printf( "           widgets: %s\n", implode( ', ', array_count_values( $m[1] ) ? array_map( fn( $w, $n ) => "$w x$n", array_keys( array_count_values( $m[1] ) ), array_count_values( $m[1] ) ) : array() ) );
	}
}
printf( "\nregistration on my-account: %s | generate username: %s | generate password: %s\n", get_option( 'woocommerce_enable_myaccount_registration' ), get_option( 'woocommerce_registration_generate_username' ), get_option( 'woocommerce_registration_generate_password' ) );
printf( "guest checkout: %s | coupons: %s | shipping calc on cart: %s\n", get_option( 'woocommerce_enable_guest_checkout' ), get_option( 'woocommerce_enable_coupons' ), get_option( 'woocommerce_enable_shipping_calc' ) );
printf( "gateways enabled: %s\n", implode( ', ', array_keys( array_filter( WC()->payment_gateways()->payment_gateways(), fn( $g ) => $g->enabled === 'yes' ) ) ) ?: '(none)' );
printf( "Elementor Pro woo widgets: cart=%s checkout=%s my-account=%s\n",
	class_exists( '\ElementorPro\Modules\Woocommerce\Widgets\Cart' ) ? 'yes' : 'no',
	class_exists( '\ElementorPro\Modules\Woocommerce\Widgets\Checkout' ) ? 'yes' : 'no',
	class_exists( '\ElementorPro\Modules\Woocommerce\Widgets\My_Account' ) ? 'yes' : 'no' );
