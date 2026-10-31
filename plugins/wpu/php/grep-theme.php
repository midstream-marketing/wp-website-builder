<?php
/** Read-only: grep the active theme (or a plugin folder) for a string.  rwpphp.ps1 php/grep-theme.php "needle" [plugins/<dir>] */
defined( 'ABSPATH' ) || exit;
$needle = (string) ( $argv[1] ?? "" );
$root   = isset( $argv[2] ) ? WP_CONTENT_DIR . "/" . $argv[2] : get_template_directory();
if ( '' === $needle ) {
	exit( "usage: needle [plugins/<dir>]\n" );
}
$it = new RecursiveIteratorIterator( new RecursiveDirectoryIterator( $root, FilesystemIterator::SKIP_DOTS ) );
$n  = 0;
foreach ( $it as $f ) {
	if ( ! preg_match( '/\.(php|js)$/', $f->getFilename() ) || preg_match( '#/(vendor|node_modules)/|\.min\.js$#', $f->getPathname() ) ) {
		continue;
	}
	foreach ( file( $f->getPathname() ) as $i => $line ) {
		if ( false !== stripos( $line, $needle ) ) {
			printf( "%s:%d  %s\n", str_replace( $root . '/', '', $f->getPathname() ), $i + 1, trim( mb_substr( $line, 0, 200 ) ) );
			if ( ++$n >= 60 ) {
				exit( "... (first 60)\n" );
			}
		}
	}
}
echo "$n hit(s)\n";
