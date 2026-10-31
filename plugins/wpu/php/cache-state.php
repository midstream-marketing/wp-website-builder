<?php
/** Read-only: which cache dropin is installed and is LiteSpeed's cache on? */
defined( 'ABSPATH' ) || exit;
$dropin = WP_CONTENT_DIR . '/advanced-cache.php';
printf( "advanced-cache.php: %s (%d bytes)\n", file_exists( $dropin ) ? 'present' : 'missing', file_exists( $dropin ) ? filesize( $dropin ) : 0 );
if ( file_exists( $dropin ) ) {
	$head = substr( (string) file_get_contents( $dropin ), 0, 400 );
	printf( "  owner hint: %s\n", preg_match( '/litespeed/i', $head ) ? 'LiteSpeed' : ( preg_match( '/airlift|blogvault|bv/i', $head ) ? 'Airlift/BlogVault' : 'unknown' ) );
}
printf( "WP_CACHE defined: %s (%s)\n", defined( 'WP_CACHE' ) ? 'yes' : 'no', defined( 'WP_CACHE' ) && WP_CACHE ? 'true' : 'false' );
printf( "litespeed.conf.cache = %s | LSCWP_V %s\n", wp_json_encode( get_option( 'litespeed.conf.cache' ) ), defined( 'LSCWP_V' ) ? LSCWP_V : '-' );
printf( "apply_airlift_optimizations = %s\n", wp_json_encode( get_option( 'apply_airlift_optimizations' ) ) );
