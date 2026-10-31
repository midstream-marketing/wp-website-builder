<?php
/**
 * Start a FULL UpdraftPlus backup in the background (WP-Cron), after making
 * sure it cannot prune the sets you need and cannot silently be DB-only.
 *
 *   powershell -File bin/rwpphp.ps1 php/updraft-backup-start.php          # dry run: show settings
 *   powershell -File bin/rwpphp.ps1 php/updraft-backup-start.php apply    # retention -> 5, includes on, start
 *
 * Then poll with php/updraft-backup-status.php. Never start a second backup
 * while one is running (two writers on one zip corrupt it) - GOTCHAS.md.
 */

defined( 'ABSPATH' ) || exit;

$apply  = in_array( 'apply', $argv ?? array(), true );
$retain = 5;

if ( ! class_exists( 'UpdraftPlus_Options' ) ) {
	exit( "UpdraftPlus is not active.\n" );
}

$running = array();
foreach ( $GLOBALS['wpdb']->get_col( "SELECT option_name FROM {$GLOBALS['wpdb']->options} WHERE option_name LIKE 'updraft_jobdata_%'" ) as $o ) {
	$jd = get_option( $o );
	if ( is_array( $jd ) && ! in_array( $jd['jobstatus'] ?? '', array( 'finished', '' ), true ) ) {
		$running[] = substr( $o, 16 ) . ' (' . $jd['jobstatus'] . ')';
	}
}

printf( "%-28s %s\n", 'retain files / db', UpdraftPlus_Options::get_updraft_option( 'updraft_retain', 2 ) . ' / ' . UpdraftPlus_Options::get_updraft_option( 'updraft_retain_db', 2 ) );
foreach ( array( 'plugins', 'themes', 'uploads', 'mu-plugins', 'others' ) as $k ) {
	printf( "%-28s %s\n", "include $k", wp_json_encode( UpdraftPlus_Options::get_updraft_option( 'updraft_include_' . $k, 1 ) ) );
}
printf( "%-28s %d\n", 'sets in history', count( (array) UpdraftPlus_Options::get_updraft_option( 'updraft_backup_history', array() ) ) );
printf( "%-28s %s\n", 'jobs not finished', $running ? implode( ', ', $running ) : 'none' );
printf( "%-28s %s\n", 'DISABLE_WP_CRON', defined( 'DISABLE_WP_CRON' ) && DISABLE_WP_CRON ? 'TRUE (cron will not fire!)' : 'no' );

if ( ! $apply ) {
	exit( "\n(dry run - 'apply' sets retention to $retain, turns every include on, and starts a full backup)\n" );
}
if ( $running ) {
	exit( "\nA job is still running - not starting another. Poll it with updraft-backup-status.php.\n" );
}

UpdraftPlus_Options::update_updraft_option( 'updraft_retain', $retain );
UpdraftPlus_Options::update_updraft_option( 'updraft_retain_db', $retain );
foreach ( array( 'plugins', 'themes', 'uploads', 'mu-plugins', 'others' ) as $k ) {
	UpdraftPlus_Options::update_updraft_option( 'updraft_include_' . $k, 1 );
}
wp_schedule_single_event( time(), 'updraft_backupnow_backup_all', array( array( 'label' => 'wpsb pre-rebuild' ) ) );
spawn_cron();
echo "\nAPPLIED: retention $retain/$retain, all includes on, full backup scheduled + cron spawned at " . gmdate( 'H:i:s' ) . " UTC.\n";
