<?php
/**
 * Read-only UpdraftPlus progress: running jobs, the newest log's last lines,
 * archives on disk and the backup history.
 *
 *   powershell -File bin/rwpphp.ps1 php/updraft-backup-status.php
 */

defined( 'ABSPATH' ) || exit;

global $wpdb;
echo "jobs:\n";
foreach ( $wpdb->get_col( "SELECT option_name FROM {$wpdb->options} WHERE option_name LIKE 'updraft_jobdata_%'" ) as $o ) {
	$jd = get_option( $o );
	printf( "  %s  status=%s  resumption=%s\n", substr( $o, 16 ), $jd['jobstatus'] ?? '?', $jd['resumption'] ?? '?' );
}

$dir  = trailingslashit( WP_CONTENT_DIR ) . 'updraft/';
$logs = glob( $dir . 'log.*.txt' ) ?: array();
usort( $logs, fn( $a, $b ) => filemtime( $b ) - filemtime( $a ) );
if ( $logs ) {
	$log = $logs[0];
	printf( "\nnewest log: %s (modified %ds ago)\n", basename( $log ), time() - filemtime( $log ) );
	$lines = file( $log, FILE_IGNORE_NEW_LINES ) ?: array();
	foreach ( array_slice( $lines, -12 ) as $l ) {
		echo '  ' . mb_strimwidth( $l, 0, 170, '…' ) . "\n";
	}
	$ok = preg_grep( '/The backup succeeded and is now complete|excluded by user|FATAL|ERROR/i', $lines );
	echo "\n  key lines:\n";
	foreach ( array_slice( $ok, -6 ) as $l ) {
		echo '    ' . mb_strimwidth( $l, 0, 170, '…' ) . "\n";
	}
}

echo "\narchives on disk (newest 12):\n";
$files = glob( $dir . 'backup_*' ) ?: array();
usort( $files, fn( $a, $b ) => filemtime( $b ) - filemtime( $a ) );
foreach ( array_slice( $files, 0, 12 ) as $f ) {
	printf( "  %-70s %8.1f MB  %s\n", basename( $f ), filesize( $f ) / 1048576, gmdate( 'Y-m-d H:i', filemtime( $f ) ) );
}

// A job whose next resumption is not in the cron array has stalled (GOTCHAS: pepcore).
echo "\nscheduled updraft events:\n";
$any = false;
foreach ( (array) _get_cron_array() as $ts => $hooks ) {
	foreach ( $hooks as $hook => $events ) {
		if ( strpos( $hook, 'updraft' ) === false ) {
			continue;
		}
		foreach ( $events as $e ) {
			$any = true;
			printf( "  %-28s due %s UTC (%+ds)  args=%s\n", $hook, gmdate( 'H:i:s', (int) $ts ), (int) $ts - time(), wp_json_encode( $e['args'] ?? array() ) );
		}
	}
}
if ( ! $any ) {
	echo "  none\n";
}

$hist = (array) get_option( 'updraft_backup_history', array() );
krsort( $hist );
echo "\nhistory (" . count( $hist ) . " sets):\n";
foreach ( $hist as $ts => $set ) {
	printf( "  %s  %s\n", gmdate( 'Y-m-d H:i', (int) $ts ), implode( ',', array_intersect( array_keys( $set ), array( 'db', 'plugins', 'themes', 'uploads', 'mu-plugins', 'others' ) ) ) );
}
