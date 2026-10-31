<?php
/**
 * Read-only WooCommerce + theme inventory: products (price, sale, stock,
 * categories, image), categories, menus with items, front page, where the
 * header/footer come from, custom CSS size, UpdraftPlus backups and retention.
 *
 *   powershell -File bin/rwpphp.ps1 php/shop-inventory.php
 */

defined( 'ABSPATH' ) || exit;

function wpsb_h( string $title ): void {
	echo "\n" . str_repeat( '=', 74 ) . "\n  " . strtoupper( $title ) . "\n" . str_repeat( '=', 74 ) . "\n";
}

wpsb_h( 'products' );
if ( function_exists( 'wc_get_products' ) ) {
	foreach ( wc_get_products( array( 'limit' => -1, 'status' => array( 'publish', 'draft', 'private' ) ) ) as $p ) {
		$cats = wp_list_pluck( get_the_terms( $p->get_id(), 'product_cat' ) ?: array(), 'name' );
		printf(
			"  %-5d %-8s %-9s %-34s reg=%-7s sale=%-7s stock=%-10s img=%-5s cats=%s  /%s/\n",
			$p->get_id(),
			$p->get_status(),
			$p->get_type(),
			mb_strimwidth( $p->get_name(), 0, 34, '…' ),
			$p->get_regular_price(),
			$p->get_sale_price(),
			$p->get_stock_status(),
			$p->get_image_id() ?: '-',
			implode( ', ', $cats ),
			$p->get_slug()
		);
		if ( $p->is_type( 'variable' ) ) {
			foreach ( $p->get_children() as $vid ) {
				$v = wc_get_product( $vid );
				printf( "         variation %-5d %-30s %s\n", $vid, implode( ' / ', $v->get_attributes() ), $v->get_price() );
			}
		}
	}
}

wpsb_h( 'product categories' );
foreach ( get_terms( array( 'taxonomy' => 'product_cat', 'hide_empty' => false ) ) as $t ) {
	printf( "  %-5d %-24s slug=%-20s count=%d thumb=%s\n", $t->term_id, $t->name, $t->slug, $t->count, get_term_meta( $t->term_id, 'thumbnail_id', true ) ?: '-' );
}

wpsb_h( 'menus' );
foreach ( wp_get_nav_menus() as $m ) {
	printf( "  %-5d %-24s slug=%s\n", $m->term_id, $m->name, $m->slug );
	foreach ( (array) wp_get_nav_menu_items( $m->term_id ) as $it ) {
		printf( "     %s- %-20s %s\n", $it->menu_item_parent ? '    ' : '', $it->title, $it->url );
	}
}
echo '  locations: ' . wp_json_encode( get_nav_menu_locations() ) . "\n";
echo '  registered: ' . wp_json_encode( array_keys( get_registered_nav_menus() ) ) . "\n";

wpsb_h( 'reading / theme' );
printf( "%-26s %s (#%d)\n", 'Front page', get_the_title( (int) get_option( 'page_on_front' ) ), (int) get_option( 'page_on_front' ) );
printf( "%-26s %s\n", 'Theme', wp_get_theme()->get( 'Name' ) . ' / parent ' . ( wp_get_theme()->parent() ? wp_get_theme()->parent()->get( 'Name' ) : '-' ) );
printf( "%-26s %s\n", 'Installed themes', implode( ', ', array_keys( wp_get_themes() ) ) );
printf( "%-26s %s\n", 'Elementor TB conditions', wp_json_encode( get_option( 'elementor_pro_theme_builder_conditions' ) ) );
printf( "%-26s %d chars\n", 'Customizer custom CSS', strlen( wp_get_custom_css() ) );
$mods = get_theme_mods();
foreach ( $mods as $k => $v ) {
	if ( preg_match( '/header|footer|logo|color|font|topbar/i', $k ) ) {
		printf( "  mod %-30s %s\n", $k, mb_strimwidth( is_scalar( $v ) ? (string) $v : wp_json_encode( $v ), 0, 110, '…' ) );
	}
}
// ThemeDraft/Doctio header & footer builder posts
foreach ( array( 'td_header', 'td_footer', 'doctio_header', 'doctio_footer', 'header', 'footer', 'elementskit_template', 'ekit_template' ) as $pt ) {
	if ( post_type_exists( $pt ) ) {
		foreach ( get_posts( array( 'post_type' => $pt, 'numberposts' => -1, 'post_status' => 'any' ) ) as $x ) {
			printf( "  %-20s #%-5d %-8s %s\n", $pt, $x->ID, $x->post_status, $x->post_title );
		}
	}
}
echo '  post types with "header|footer|template" in name: ' . implode( ', ', array_filter( get_post_types(), fn( $t ) => preg_match( '/head|foot|templ|mega/i', $t ) ) ) . "\n";

wpsb_h( 'woocommerce settings' );
foreach ( array( 'woocommerce_currency', 'woocommerce_default_country', 'woocommerce_specific_allowed_countries', 'woocommerce_calc_taxes', 'woocommerce_prices_include_tax', 'woocommerce_enable_guest_checkout', 'woocommerce_enable_myaccount_registration', 'woocommerce_coming_soon', 'woocommerce_store_pages_only' ) as $o ) {
	printf( "  %-44s %s\n", $o, wp_json_encode( get_option( $o ) ) );
}
$cart_id = (int) get_option( 'woocommerce_cart_page_id' );
$co_id   = (int) get_option( 'woocommerce_checkout_page_id' );
printf( "  cart page uses block: %s | checkout page uses block: %s\n",
	has_block( 'woocommerce/cart', $cart_id ) ? 'yes' : 'no (shortcode?)',
	has_block( 'woocommerce/checkout', $co_id ) ? 'yes' : 'no (shortcode?)' );
printf( "  checkout content: %s\n", mb_strimwidth( trim( get_post_field( 'post_content', $co_id ) ), 0, 120, '…' ) );

wpsb_h( 'updraftplus' );
$hist = (array) get_option( 'updraft_backup_history', array() );
krsort( $hist );
printf( "  backup sets: %d | retain files: %s | retain db: %s | remote: %s\n",
	count( $hist ), get_option( 'updraft_retain', '?' ), get_option( 'updraft_retain_db', '?' ), wp_json_encode( get_option( 'updraft_service' ) ) );
foreach ( array_slice( $hist, 0, 5, true ) as $ts => $set ) {
	printf( "   - %s  %s\n", gmdate( 'Y-m-d H:i', (int) $ts ), implode( ',', array_keys( array_filter( $set, 'is_array' ) ) ) );
}
