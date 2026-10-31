<?php
/**
 * Turn measures of the WPU Hardening mu-plugin on or off. Dry run by default.
 *
 *   powershell -File scripts/rwpphp.ps1 php/hardening-set.php                                  show current state
 *   powershell -File scripts/rwpphp.ps1 php/hardening-set.php on=no_file_edit,headers          dry run
 *   powershell -File scripts/rwpphp.ps1 php/hardening-set.php on=no_file_edit,headers apply    make it
 *   powershell -File scripts/rwpphp.ps1 php/hardening-set.php off=no_xmlrpc apply
 *
 * Needs mu-plugins/wpu-hardening.php installed first:
 *   powershell -File scripts/rfile.ps1 put <plugin>/site-plugins/wpu-hardening.php mu-plugins/wpu-hardening.php
 */
defined( 'ABSPATH' ) || exit;

$known = array( 'no_file_edit', 'no_xmlrpc', 'no_user_listing', 'no_author_scan', 'hide_version', 'headers' );
$args  = (array) ( $argv ?? array() );
$apply = in_array( 'apply', $args, true );
$on    = array();
$off   = array();
foreach ( $args as $a ) {
	if ( preg_match( '/^(on|off)=([a-z_,]+)$/', (string) $a, $m ) ) {
		foreach ( explode( ',', $m[2] ) as $k ) {
			if ( ! in_array( $k, $known, true ) ) {
				exit( "unknown measure '$k'. Known: " . implode( ', ', $known ) . "\n" );
			}
			if ( 'on' === $m[1] ) {
				$on[] = $k;
			} else {
				$off[] = $k;
			}
		}
	}
}

require_once ABSPATH . 'wp-admin/includes/plugin.php';
$installed = array_key_exists( 'wpu-hardening.php', get_mu_plugins() );
printf( "mu-plugin wpu-hardening.php: %s\n\n", $installed ? 'installed' : 'NOT INSTALLED - measures below have no effect until it is' );

$cur = get_option( 'wpu_hardening', array() );
$cur = is_array( $cur ) ? $cur : array();
$new = $cur;
foreach ( $on as $k ) {
	$new[ $k ] = 1;
}
foreach ( $off as $k ) {
	unset( $new[ $k ] );
}
foreach ( $known as $k ) {
	$a = ! empty( $cur[ $k ] );
	$b = ! empty( $new[ $k ] );
	printf( "  %s %-16s %s%s\n", $a === $b ? '=' : '~', $k, $a ? 'on' : 'off', $a === $b ? '' : ' -> ' . ( $b ? 'on' : 'off' ) );
}
if ( $new === $cur ) {
	exit( "\nno change.\n" );
}
if ( $apply ) {
	update_option( 'wpu_hardening', $new, true );
	do_action( 'litespeed_purge_all' );
	echo "\nAPPLIED. Verify from outside: python tools/security/outside.py\n";
} else {
	echo "\n(dry run - add 'apply')\n";
}
