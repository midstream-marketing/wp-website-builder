<?php
/**
 * Read-only: is a plugin's code intact on disk? Uses PHP filesystem calls only.
 *  - folder exists, total files, newest/oldest mtimes, files changed in the last N minutes
 *  - specific files that must exist (arguments after the slug)
 *  - update in progress? (core/auto updater locks, wp-content/upgrade contents)
 *  - quarantine hints (.imunify*, *.quarantine, suspicious renames next to missing files)
 *
 *   powershell -File bin/rwpphp.ps1 php/plugin-files.php <plugin-slug> [relative/file.php ...]
 */

defined( 'ABSPATH' ) || exit;

$args = array_slice( $argv ?? array(), 1 );
$slug = preg_replace( '/[^a-z0-9_-]/i', '', (string) array_shift( $args ) );
$root = WP_PLUGIN_DIR . '/' . $slug;

printf( "plugin folder: %s  %s\n", str_replace( ABSPATH, '', $root ), is_dir( $root ) ? 'EXISTS' : 'MISSING' );
if ( ! is_dir( $root ) ) {
	return;
}

$total  = 0;
$recent = array();
$newest = 0;
$oldest = PHP_INT_MAX;
$window = 90 * 60;
$it     = new RecursiveIteratorIterator( new RecursiveDirectoryIterator( $root, FilesystemIterator::SKIP_DOTS ) );
foreach ( $it as $f ) {
	if ( ! $f->isFile() ) {
		continue;
	}
	$total++;
	$m      = $f->getMTime();
	$newest = max( $newest, $m );
	$oldest = min( $oldest, $m );
	if ( time() - $m < $window ) {
		$recent[] = str_replace( $root . '/', '', $f->getPathname() ) . '  (' . ( time() - $m ) . 's ago)';
	}
	if ( preg_match( '/\.(quarantine|imunify|infected|suspected)|\.php\.[a-z0-9]{6,}$/i', $f->getFilename() ) ) {
		echo '  QUARANTINE-LIKE: ' . str_replace( $root . '/', '', $f->getPathname() ) . "\n";
	}
}
printf( "files: %d   oldest mtime %s   newest %s UTC\n", $total, gmdate( 'Y-m-d H:i', $oldest ), gmdate( 'Y-m-d H:i', $newest ) );
printf( "changed in the last %d min: %d\n", $window / 60, count( $recent ) );
foreach ( array_slice( $recent, 0, 15 ) as $r ) {
	echo "  $r\n";
}

echo "\nrequired files:\n";
foreach ( $args as $rel ) {
	$p = $root . '/' . ltrim( $rel, '/' );
	printf( "  %-70s %s\n", $rel, is_file( $p ) ? 'present (' . filesize( $p ) . ' B)' : 'MISSING' );
	$dir = dirname( $p );
	if ( ! is_file( $p ) && is_dir( $dir ) ) {
		echo '    folder now holds: ' . implode( ', ', array_slice( array_diff( scandir( $dir ), array( '.', '..' ) ), 0, 20 ) ) . "\n";
	}
}

echo "\nupdates in progress:\n";
foreach ( array( 'core_updater.lock', 'auto_updater.lock' ) as $o ) {
	$v = get_option( $o );
	printf( "  %-20s %s\n", $o, $v ? 'SET ' . gmdate( 'H:i:s', (int) $v ) . ' UTC' : 'none' );
}
$up = WP_CONTENT_DIR . '/upgrade';
echo '  wp-content/upgrade: ' . ( is_dir( $up ) ? implode( ', ', array_slice( array_diff( scandir( $up ), array( '.', '..' ) ), 0, 10 ) ) ?: '(empty)' : '(no folder)' ) . "\n";
$upd = get_site_transient( 'update_plugins' );
foreach ( (array) ( $upd->response ?? array() ) as $file => $info ) {
	if ( strpos( $file, $slug ) === 0 ) {
		printf( "  update available: %s -> %s\n", $file, $info->new_version ?? '?' );
	}
}
printf( "  auto-updates enabled for plugins: %s\n", wp_json_encode( array_values( array_filter( (array) get_site_option( 'auto_update_plugins', array() ), fn( $p ) => strpos( $p, $slug ) === 0 ) ) ) );
