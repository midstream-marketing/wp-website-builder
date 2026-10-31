<?php
/**
 * Database backup that does not depend on a backup plugin: mysqldump of this
 * site's database, gzipped into wp-content/updraft/ (UpdraftPlus's folder,
 * already denied to the web by its .htaccess / index.php), for download with
 * bin/rfile.ps1 get. Needs exec() and a mysqldump binary on the host.
 *
 *   powershell -File bin/rwpphp.ps1 php/db-dump.php          # dry run: checks only
 *   powershell -File bin/rwpphp.ps1 php/db-dump.php apply    # write the dump
 *   powershell -File bin/rwpphp.ps1 php/db-dump.php delete <file>   # remove it after download
 */

defined( 'ABSPATH' ) || exit;

$args  = array_slice( $argv ?? array(), 1 );
$apply = in_array( 'apply', $args, true );
$dir   = trailingslashit( WP_CONTENT_DIR ) . 'updraft/';

if ( ( $args[0] ?? '' ) === 'delete' ) {
	$f = basename( (string) ( $args[1] ?? '' ) );
	if ( ! preg_match( '/^wp(sb|u)-db-[0-9a-z_-]+\.sql\.gz$/i', $f ) || ! is_file( $dir . $f ) ) {
		exit( "refusing: not a wpsb dump in updraft/: $f\n" );
	}
	unlink( $dir . $f );
	exit( "deleted updraft/$f\n" );
}

$disabled = array_map( 'trim', explode( ',', (string) ini_get( 'disable_functions' ) ) );
if ( ! function_exists( 'exec' ) || in_array( 'exec', $disabled, true ) ) {
	exit( "exec() is not available here - use UpdraftPlus or the host's backup instead.\n" );
}

$bin = trim( (string) shell_exec( 'command -v mysqldump 2>/dev/null' ) );
printf( "mysqldump      : %s\n", $bin ?: 'NOT FOUND' );
printf( "database       : %s @ %s (prefix %s)\n", DB_NAME, DB_HOST, $GLOBALS['wpdb']->prefix );
printf( "target folder  : wp-content/updraft/ (%s)\n", is_writable( $dir ) ? 'writable' : 'NOT writable' );
printf( "folder guarded : %s\n", file_exists( $dir . '.htaccess' ) ? '.htaccess present' : 'no .htaccess!' );
$tables = $GLOBALS['wpdb']->get_col( 'SHOW TABLES' );
$size   = (float) $GLOBALS['wpdb']->get_var( $GLOBALS['wpdb']->prepare( 'SELECT SUM(data_length + index_length) FROM information_schema.TABLES WHERE table_schema = %s', DB_NAME ) );
printf( "tables / size  : %d tables, %.1f MB on disk\n", count( $tables ), $size / 1048576 );

if ( ! $bin ) {
	exit( "\nno mysqldump binary - nothing done.\n" );
}
if ( ! $apply ) {
	exit( "\n(dry run - 'apply' writes wp-content/updraft/wpu-db-<timestamp>-<random>.sql.gz)\n" );
}

// Credentials go through a temporary option file, never on the command line (ps would show them).
$host = DB_HOST;
$port = '';
if ( strpos( $host, ':' ) !== false ) {
	list( $host, $port ) = explode( ':', $host, 2 );
}
$cnf = tempnam( sys_get_temp_dir(), 'wpsb' );
file_put_contents( $cnf, "[client]\nuser=\"" . DB_USER . "\"\npassword=\"" . str_replace( '"', '\\"', DB_PASSWORD ) . "\"\nhost=\"" . $host . "\"\n" . ( $port !== '' && ctype_digit( $port ) ? "port=$port\n" : '' ) . ( $port !== '' && ! ctype_digit( $port ) ? "socket=\"$port\"\n" : '' ) );
chmod( $cnf, 0600 );

// Random suffix: on nginx the .htaccess guard is ignored, so the name must not be guessable.
$file = 'wpu-db-' . gmdate( 'Ymd-His' ) . '-' . bin2hex( random_bytes( 8 ) ) . '.sql.gz';
$cmd  = sprintf(
	'%s --defaults-extra-file=%s --single-transaction --quick --routines --triggers --no-tablespaces --default-character-set=utf8mb4 %s 2>%s | gzip -6 > %s',
	escapeshellarg( $bin ),
	escapeshellarg( $cnf ),
	escapeshellarg( DB_NAME ),
	escapeshellarg( $dir . $file . '.err' ),
	escapeshellarg( $dir . $file )
);
$t0 = microtime( true );
exec( $cmd, $out, $rc );
unlink( $cnf );

$err = is_file( $dir . $file . '.err' ) ? trim( (string) file_get_contents( $dir . $file . '.err' ) ) : '';
@unlink( $dir . $file . '.err' );

clearstatcache();
$bytes = is_file( $dir . $file ) ? filesize( $dir . $file ) : 0;
printf( "\nwrote updraft/%s  %.2f MB gz in %.1fs  rc=%d\n", $file, $bytes / 1048576, microtime( true ) - $t0, $rc );
if ( $err ) {
	echo "mysqldump said: " . mb_strimwidth( $err, 0, 400, '…' ) . "\n";
}

// Sanity: the dump must end with mysqldump's completion marker and name every table.
$tail = (string) shell_exec( 'gzip -dc ' . escapeshellarg( $dir . $file ) . ' | tail -c 300' );
$made = (int) trim( (string) shell_exec( 'gzip -dc ' . escapeshellarg( $dir . $file ) . " | grep -c '^CREATE TABLE'" ) );
printf( "completion marker: %s | CREATE TABLE statements: %d of %d tables\n", strpos( $tail, 'Dump completed' ) !== false ? 'yes' : 'NO', $made, count( $tables ) );
echo ( strpos( $tail, 'Dump completed' ) !== false && $made === count( $tables ) ) ? "OK - download it, then delete it from the server.\n" : "! dump looks incomplete - do not rely on it.\n";
