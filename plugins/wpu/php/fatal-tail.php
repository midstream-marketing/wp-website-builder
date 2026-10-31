<?php
/**
 * Read-only: the last few entries of the newest WooCommerce fatal-error logs, untruncated, so the file and
 * line of each error are visible (site-info.php cuts them short).
 *   powershell -File bin/rwpphp.ps1 php/fatal-tail.php [count]
 */
defined( 'ABSPATH' ) || exit;

$n    = 4;
$args = (array) ( $argv ?? array() );
foreach ( $args as $a ) {
	if ( ctype_digit( (string) $a ) ) {
		$n = (int) $a;
	}
}
$dir = defined( 'WC_LOG_DIR' ) ? WC_LOG_DIR : WP_CONTENT_DIR . '/uploads/wc-logs/';
$files = glob( trailingslashit( $dir ) . 'fatal-errors-*.log' ) ?: array();
usort( $files, fn( $a, $b ) => filemtime( $b ) <=> filemtime( $a ) );
foreach ( array_slice( $files, 0, 2 ) as $f ) {
	printf( "== %s (modified %s UTC)\n", basename( $f ), gmdate( 'Y-m-d H:i', filemtime( $f ) ) );
	$lines = preg_split( '/\R/', (string) file_get_contents( $f ) );
	$lines = array_values( array_filter( $lines, 'strlen' ) );
	foreach ( array_slice( $lines, -$n ) as $l ) {
		// strip the absolute install path so the output stays readable
		echo '  ' . str_replace( ABSPATH, '/', substr( $l, 0, 900 ) ) . "\n";
	}
	echo "\n";
}
