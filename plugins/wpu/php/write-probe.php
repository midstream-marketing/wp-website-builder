<?php
/**
 * Read-mostly diagnostic: why does writing into a wp-content folder fail? Tries a .txt and a .php file
 * with file_put_contents and with WP_Filesystem, reports the PHP error for each, then removes the test
 * files. Touches only wpsb-probe.* in the given folder.
 *   powershell -File bin/rwpphp.ps1 php/write-probe.php apply plugins/cas-store/includes
 */
defined( 'ABSPATH' ) || exit;

$args = (array) ( $argv ?? array() );
$rel  = 'uploads';
foreach ( $args as $a ) {
	if ( 'apply' !== $a && '' !== (string) $a && ! str_ends_with( (string) $a, '.php' ) && ! preg_match( '#(^|/)\.\.(/|$)#', (string) $a ) ) {
		$rel = (string) $a;
	}
}
$dir = trailingslashit( WP_CONTENT_DIR ) . trim( $rel, '/' );
printf( "dir %s exists=%s writable=%s perms=%s owner=%s php-user=%s\n", $rel, is_dir( $dir ) ? 'y' : 'n', is_writable( $dir ) ? 'y' : 'n', substr( sprintf( '%o', @fileperms( $dir ) ), -4 ), function_exists( 'posix_getpwuid' ) ? ( posix_getpwuid( @fileowner( $dir ) )['name'] ?? '?' ) : @fileowner( $dir ), function_exists( 'posix_geteuid' ) ? ( posix_getpwuid( posix_geteuid() )['name'] ?? '?' ) : get_current_user() );
printf( "disable_functions: %s\nopen_basedir: %s\nFS method: %s\n", ini_get( 'disable_functions' ) ?: '(none)', ini_get( 'open_basedir' ) ?: '(none)', function_exists( 'get_filesystem_method' ) ? get_filesystem_method() : '?' );

foreach ( array( 'wpsb-probe.txt' => "hello\n", 'wpsb-probe.php' => "<?php\n// probe\n" ) as $name => $body ) {
	$f = $dir . '/' . $name;
	error_clear_last();
	$n   = @file_put_contents( $f, $body );
	$err = error_get_last();
	printf( "  file_put_contents %-16s %s%s\n", $name, false === $n ? 'FAILED' : "ok ({$n} bytes)", false === $n && $err ? ' - ' . $err['message'] : '' );
	if ( false !== $n ) {
		@unlink( $f );
	}
}

require_once ABSPATH . 'wp-admin/includes/file.php';
if ( WP_Filesystem() ) {
	global $wp_filesystem;
	$f  = $dir . '/wpsb-probe.php';
	$ok = $wp_filesystem->put_contents( $f, "<?php\n// probe\n", FS_CHMOD_FILE );
	printf( "  WP_Filesystem put_contents .php: %s\n", $ok ? 'ok' : 'FAILED' );
	if ( $ok ) {
		$wp_filesystem->delete( $f );
	}
}
