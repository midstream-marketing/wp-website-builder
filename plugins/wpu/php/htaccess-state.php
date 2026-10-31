<?php
/** Read-only: are the LSCache rules still in .htaccess? */
defined( 'ABSPATH' ) || exit;
$f = ABSPATH . '.htaccess';
printf( ".htaccess: %s (%d bytes, writable: %s)\n", file_exists( $f ) ? 'present' : 'missing', file_exists( $f ) ? filesize( $f ) : 0, is_writable( $f ) ? 'yes' : 'no' );
if ( ! file_exists( $f ) ) {
	exit;
}
$src = (string) file_get_contents( $f );
printf( "LSCACHE marker: %s | CacheLookup: %s | Airlift/bv marker: %s\n",
	false !== strpos( $src, 'LSCACHE' ) ? 'yes' : 'NO',
	false !== stripos( $src, 'CacheLookup' ) ? 'yes' : 'NO',
	preg_match( '/airlift|blogvault|bv_/i', $src ) ? 'yes' : 'no' );
foreach ( explode( "\n", $src ) as $i => $l ) {
	if ( preg_match( '/LSCACHE|CacheLookup|IfModule|airlift/i', $l ) ) {
		printf( "  %3d %s\n", $i + 1, mb_strimwidth( trim( $l ), 0, 110 ) );
	}
}
