<?php
/** Read-only: Elementor / Pro versions, licence, active experiments, registered widget count, HFE templates, kit globals. */
defined( 'ABSPATH' ) || exit;
printf( "Elementor %s | Pro %s | licence %s\n", defined( 'ELEMENTOR_VERSION' ) ? ELEMENTOR_VERSION : '-', defined( 'ELEMENTOR_PRO_VERSION' ) ? ELEMENTOR_PRO_VERSION : '-', class_exists( '\ElementorPro\License\API' ) ? ( \ElementorPro\License\API::is_license_active() ? 'active' : 'NOT active' ) : '-' );
$exp = \Elementor\Plugin::$instance->experiments;
foreach ( array( 'container', 'nested-elements', 'mega-menu', 'e_optimized_markup', 'e_font_icon_svg', 'loop', 'taxonomy-filter' ) as $f ) {
	printf( "  experiment %-20s %s\n", $f, $exp->get_features( $f ) ? ( $exp->is_feature_active( $f ) ? 'active' : 'inactive' ) : 'n/a' );
}
$w = \Elementor\Plugin::$instance->widgets_manager->get_widget_types();
$names = array_keys( $w );
printf( "widgets: %d\n  pro/woo sample: %s\n", count( $names ), implode( ' ', array_values( array_filter( $names, fn( $n ) => preg_match( '/^(mega-menu|n-menu|nav-menu|loop|woocommerce-products|form|n-carousel|n-tabs|media-carousel|call-to-action|flip-box|price-list|hotspot|taxonomy|search)/', $n ) ) ) ) );
printf( "  mixxcazt widgets: %s\n", implode( ' ', array_values( array_filter( $names, fn( $n ) => 0 === strpos( $n, 'mixxcazt' ) ) ) ) );
foreach ( get_posts( array( 'post_type' => 'elementor-hf', 'numberposts' => -1, 'post_status' => 'any' ) ) as $p ) {
	printf( "HFE #%d %s [%s] %s\n", $p->ID, $p->post_title, $p->post_status, get_post_meta( $p->ID, 'ehf_template_type', true ) );
}
$kit = \Elementor\Plugin::$instance->kits_manager->get_active_kit_for_frontend();
$s   = $kit ? $kit->get_settings() : array();
foreach ( array( 'system_colors', 'custom_colors', 'system_typography' ) as $k ) {
	echo "$k: " . wp_json_encode( array_map( fn( $c ) => ( $c['title'] ?? '' ) . '=' . ( $c['color'] ?? ( $c['typography_font_family'] ?? '' ) ), (array) ( $s[ $k ] ?? array() ) ) ) . "\n";
}
