<?php
/**
 * Read-only: time each page FROM THE SERVER ITSELF (loopback), so the numbers
 * contain no network distance from the person measuring. For each URL:
 *   - a cache-bypassing request (unique query string + no-cache header) = build time
 *   - two normal requests = cache hit time (x-litespeed-cache header shown)
 *
 *   powershell -File bin/rwpphp.ps1 php/server-timing.php [/path/ ...]
 */

defined( 'ABSPATH' ) || exit;

$paths = array_slice( $argv ?? array(), 1 );
if ( ! $paths ) {
	$paths = array( '/', '/services/', '/contact/', '/book/' );
}

$get = function ( string $url, array $headers ) {
	$t0 = microtime( true );
	$r  = wp_remote_get( $url, array( 'timeout' => 45, 'redirection' => 0, 'sslverify' => false, 'headers' => $headers ) ); // wpsec:ignore - self-fetch: every URL is home_url(), redirects off; the safe variant blocks loopback on many hosts.
	$ms = ( microtime( true ) - $t0 ) * 1000;
	if ( is_wp_error( $r ) ) {
		return array( $ms, 'ERR ' . $r->get_error_message(), '', 0 );
	}
	return array( $ms, wp_remote_retrieve_response_code( $r ), (string) wp_remote_retrieve_header( $r, 'x-litespeed-cache' ), strlen( wp_remote_retrieve_body( $r ) ) );
};

printf( "%-12s %-24s %-24s %-24s\n", 'page', 'bypass (build)', 'normal #1', 'normal #2' );
foreach ( $paths as $p ) {
	$url = home_url( $p );
	$a   = $get( add_query_arg( 'wpsbnc', wp_generate_password( 8, false ), $url ), array( 'Cache-Control' => 'no-cache', 'Pragma' => 'no-cache' ) );
	$b   = $get( $url, array() );
	$c   = $get( $url, array() );
	$f   = fn( $x ) => sprintf( '%5.0fms %s %-4s', $x[0], $x[1], $x[2] ?: '-' );
	printf( "%-12s %-24s %-24s %-24s  %d KB\n", $p, $f( $a ), $f( $b ), $f( $c ), $c[3] / 1024 );
}
