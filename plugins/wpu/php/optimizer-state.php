<?php
/** Read-only: which optimizer is delaying CSS (bv_inline_delayed_css / al_opt)? */
defined( 'ABSPATH' ) || exit;
require_once ABSPATH . 'wp-admin/includes/plugin.php';

echo "plugins matching airlift/blogvault/bv/optimiz:\n";
foreach ( get_plugins() as $file => $d ) {
	if ( preg_match( '/airlift|blogvault|bvplugin|optimiz|speed|cache|migrate/i', $file . ' ' . $d['Name'] ) ) {
		printf( "  %-8s %-46s %s\n", is_plugin_active( $file ) ? 'ACTIVE' : 'inactive', $file, $d['Version'] );
	}
}
echo "\nmu-plugins: " . implode( ', ', array_keys( get_mu_plugins() ) ) . "\n";
echo "\ndropins: " . implode( ', ', array_keys( get_dropins() ) ) . "\n";

global $wpdb;
echo "\noptions matching airlift/bv_/blogvault:\n";
foreach ( $wpdb->get_results( "SELECT option_name, LENGTH(option_value) len, autoload FROM {$wpdb->options} WHERE option_name REGEXP '^(bv_|airlift|blogvault|al_)' ORDER BY option_name LIMIT 40" ) as $r ) {
	printf( "  %-44s %6d bytes  autoload=%s\n", $r->option_name, $r->len, $r->autoload );
}
foreach ( array( 'airlift_settings', 'airlift_options', 'bv_airlift_settings' ) as $o ) {
	$v = get_option( $o );
	if ( $v ) {
		printf( "\n%s = %s\n", $o, mb_strimwidth( wp_json_encode( $v ), 0, 900, '…' ) );
	}
}
printf( "\nconstants: AIRLIFT %s | BV %s\n", defined( 'AIRLIFT_VERSION' ) ? AIRLIFT_VERSION : '-', defined( 'BV_PLUGIN_VERSION' ) ? BV_PLUGIN_VERSION : '-' );
