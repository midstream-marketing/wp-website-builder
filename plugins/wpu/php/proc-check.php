<?php
/**
 * Read-only: can PHP see this account's processes (e.g. a zip left running by
 * a backup), and which process functions does the host disable? Lists
 * matching processes only - never signals or kills anything.
 *
 *   powershell -File bin/rwpphp.ps1 php/proc-check.php [pattern]     (default: zip)
 */

defined( 'ABSPATH' ) || exit;

$pattern  = preg_replace( '/[^a-z0-9._-]/i', '', $argv[1] ?? 'zip' ) ?: 'zip';
$disabled = array_filter( array_map( 'trim', explode( ',', (string) ini_get( 'disable_functions' ) ) ) );

printf( "PHP user        : %s\n", function_exists( 'posix_getpwuid' ) && function_exists( 'posix_geteuid' ) ? ( posix_getpwuid( posix_geteuid() )['name'] ?? '?' ) : get_current_user() );
printf( "max_execution   : %s\n", ini_get( 'max_execution_time' ) );
foreach ( array( 'exec', 'shell_exec', 'proc_open', 'popen', 'passthru', 'system', 'posix_kill', 'proc_nice' ) as $f ) {
	printf( "  %-12s %s\n", $f, ! function_exists( $f ) ? 'not available' : ( in_array( $f, $disabled, true ) ? 'DISABLED' : 'available' ) );
}

$run = null;
if ( function_exists( 'exec' ) && ! in_array( 'exec', $disabled, true ) ) {
	$run = function ( string $cmd ) {
		$out = array();
		exec( $cmd . ' 2>&1', $out );
		return $out;
	};
} elseif ( function_exists( 'shell_exec' ) && ! in_array( 'shell_exec', $disabled, true ) ) {
	$run = fn( string $cmd ) => explode( "\n", trim( (string) shell_exec( $cmd . ' 2>&1' ) ) );
}

if ( ! $run ) {
	echo "\nno process access from PHP - the host (or cPanel) has to look at running processes.\n";
	return;
}

echo "\nprocesses of this account matching '$pattern':\n";
$lines = $run( 'ps -u "$(id -un)" -o pid,ppid,etime,pcpu,pmem,stat,args' );
$head  = array_shift( $lines );
echo "  $head\n";
$n = 0;
foreach ( $lines as $l ) {
	if ( stripos( $l, $pattern ) !== false && stripos( $l, 'ps -u' ) === false ) {
		echo '  ' . mb_strimwidth( $l, 0, 220, '…' ) . "\n";
		$n++;
	}
}
echo $n ? '' : "  none\n";

$dir = trailingslashit( WP_CONTENT_DIR ) . 'updraft/';
foreach ( glob( $dir . '*.zip.tmp' ) ?: array() as $f ) {
	clearstatcache( true, $f );
	printf( "\n%s  %.1f MB  modified %ds ago\n", basename( $f ), filesize( $f ) / 1048576, time() - filemtime( $f ) );
}
