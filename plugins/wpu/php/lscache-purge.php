<?php
/**
 * Purge LiteSpeed Cache (all pages) + Elementor's generated CSS. Run after uploading an mu-plugin
 * that prints inline CSS: cached pages keep serving the old CSS until purged.
 *
 *   powershell -File bin/rwpphp.ps1 php/lscache-purge.php          # dry run
 *   powershell -File bin/rwpphp.ps1 php/lscache-purge.php apply
 */

defined( 'ABSPATH' ) || exit;

printf( "LiteSpeed Cache active: %s\n", defined( 'LSCWP_V' ) ? 'yes ' . LSCWP_V : 'no' );
if ( ! in_array( 'apply', $argv ?? array(), true ) ) {
	exit( "(dry run - 'apply' purges all cached pages)\n" );
}
do_action( 'litespeed_purge_all' );
if ( class_exists( '\Elementor\Plugin' ) ) {
	\Elementor\Plugin::$instance->files_manager->clear_cache();
}
echo "PURGED.\n";
