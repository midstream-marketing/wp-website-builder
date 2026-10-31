<?php
/**
 * Read-only speed snapshot: server cache capability, caching plugins,
 * Elementor performance options/experiments, Amelia async loading, autoload
 * size, and the heaviest registered front-end assets on the home page.
 *
 *   powershell -File bin/rwpphp.ps1 php/speed-info.php
 */

defined( 'ABSPATH' ) || exit;

function wpsb_h( string $t ): void {
	echo "\n" . str_repeat( '=', 74 ) . "\n  " . strtoupper( $t ) . "\n" . str_repeat( '=', 74 ) . "\n";
}

wpsb_h( 'server' );
printf( "%-28s %s\n", 'SERVER_SOFTWARE', $_SERVER['SERVER_SOFTWARE'] ?? '?' );
printf( "%-28s %s\n", 'LSWS edition', $_SERVER['LSWS_EDITION'] ?? '(not set)' );
printf( "%-28s %s\n", 'X-LSCACHE env', isset( $_SERVER['X-LSCACHE'] ) || isset( $_SERVER['HTTP_X_LSCACHE'] ) ? 'present' : '(not set - normal outside a cached request)' );
printf( "%-28s %s\n", 'OPcache', function_exists( 'opcache_get_status' ) && @opcache_get_status( false ) ? 'on' : 'off/unknown' );
printf( "%-28s %s\n", 'object cache', wp_using_ext_object_cache() ? 'external' : 'none' );
$ht = ABSPATH . '.htaccess';
printf( "%-28s %s\n", '.htaccess LSCache rules', is_readable( $ht ) && strpos( (string) file_get_contents( $ht ), 'LSCACHE' ) !== false ? 'present' : 'none' );

wpsb_h( 'caching / optimisation plugins' );
require_once ABSPATH . 'wp-admin/includes/plugin.php';
foreach ( get_plugins() as $file => $p ) {
	if ( preg_match( '/cache|litespeed|rocket|autoptimize|perfmatters|optimi|minif|speed|swift|hummingbird|flying/i', $file . ' ' . $p['Name'] ) ) {
		printf( "  %-50s %-8s %s\n", $file, $p['Version'], is_plugin_active( $file ) ? 'active' : 'inactive' );
	}
}

wpsb_h( 'elementor performance' );
foreach ( array( 'elementor_local_google_fonts', 'elementor_font_display', 'elementor_css_print_method', 'elementor_google_font', 'elementor_load_fa4_shim', 'elementor_lazy_load_background_images', 'elementor_element_cache_ttl', 'elementor_optimized_image_loading', 'elementor_optimized_gutenberg_loading', 'elementor_unfiltered_files_upload' ) as $o ) {
	printf( "  %-44s %s\n", $o, wp_json_encode( get_option( $o, '(unset)' ) ) );
}
global $wpdb;
foreach ( $wpdb->get_results( "SELECT option_name, option_value FROM {$wpdb->options} WHERE option_name LIKE 'elementor_experiment-%' ORDER BY option_name" ) as $r ) {
	printf( "  %-44s %s\n", $r->option_name, $r->option_value );
}

wpsb_h( 'amelia' );
$s = json_decode( (string) get_option( 'amelia_settings' ), true );
printf( "  %-28s %s\n", 'activation.v3AsyncLoading', wp_json_encode( $s['activation']['v3AsyncLoading'] ?? null ) );
printf( "  %-28s %s\n", 'activation.v3RelativePath', wp_json_encode( $s['activation']['v3RelativePath'] ?? null ) );

wpsb_h( 'database' );
$auto = (int) $wpdb->get_var( "SELECT SUM(LENGTH(option_value)) FROM {$wpdb->options} WHERE autoload IN ('yes','on','auto-on','auto')" );
printf( "  autoloaded options: %.1f KB\n", $auto / 1024 );
foreach ( $wpdb->get_results( "SELECT option_name, LENGTH(option_value) AS len FROM {$wpdb->options} WHERE autoload IN ('yes','on','auto-on','auto') ORDER BY len DESC LIMIT 6" ) as $r ) {
	printf( "    %-50s %7.1f KB\n", $r->option_name, $r->len / 1024 );
}
printf( "  transients: %d rows\n", (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$wpdb->options} WHERE option_name LIKE '\\_transient\\_%'" ) );
printf( "  revisions: %d\n", (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type = 'revision'" ) );
