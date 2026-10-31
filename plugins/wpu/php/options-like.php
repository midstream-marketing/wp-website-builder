<?php
/**
 * Read-only: print options whose name matches a SQL LIKE pattern, with values
 * (long values shortened, obvious secrets masked).
 *
 *   powershell -File bin/rwpphp.ps1 php/options-like.php "litespeed.conf.%" [filterRegex]
 */

defined( 'ABSPATH' ) || exit;

$args    = array_slice( $argv ?? array(), 1 );
$pattern = (string) ( $args[0] ?? '' );
$filter  = (string) ( $args[1] ?? '' );
if ( $pattern === '' ) {
	exit( "usage: options-like.php <LIKE pattern> [filterRegex]\n" );
}

global $wpdb;
$rows = $wpdb->get_results( $wpdb->prepare( "SELECT option_name, option_value FROM {$wpdb->options} WHERE option_name LIKE %s ORDER BY option_name", $pattern ) );
printf( "%d option(s) like %s\n", count( $rows ), $pattern );
foreach ( $rows as $r ) {
	if ( $filter && ! preg_match( '/' . str_replace( '/', '\/', $filter ) . '/i', $r->option_name ) ) {
		continue;
	}
	$v = $r->option_value;
	if ( preg_match( '/key|secret|token|pass|api/i', $r->option_name ) && $v !== '' ) {
		$v = '***set(' . strlen( $v ) . ')***';
	}
	printf( "  %-52s %s\n", $r->option_name, mb_strimwidth( str_replace( array( "\r", "\n" ), ' ', $v ), 0, 110, '…' ) );
}
