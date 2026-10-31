<?php
/**
 * Read-only: print the full settings of Elementor elements in one post,
 * found by element id (and their direct children's ids/types).
 *
 *   powershell -File bin/rwpphp.ps1 php/el-settings.php <postId> <elementId> [<elementId> ...]
 */

defined( 'ABSPATH' ) || exit;

$args = array_slice( $argv ?? array(), 1 );
$post = (int) array_shift( $args );
if ( ! $post || ! $args ) {
	exit( "usage: el-settings.php <postId> <elementId> [...]\n" );
}
$data = json_decode( (string) get_post_meta( $post, '_elementor_data', true ), true );
if ( ! is_array( $data ) ) {
	exit( "#$post has no readable Elementor data\n" );
}

$find = function ( array $els, string $id ) use ( &$find ) {
	foreach ( $els as $e ) {
		if ( ( $e['id'] ?? '' ) === $id ) {
			return $e;
		}
		$hit = $find( $e['elements'] ?? array(), $id );
		if ( $hit ) {
			return $hit;
		}
	}
	return null;
};

foreach ( $args as $id ) {
	$e = $find( $data, $id );
	echo "\n=== #$post / $id " . ( $e ? ( $e['widgetType'] ?? $e['elType'] ) : 'NOT FOUND' ) . "\n";
	if ( ! $e ) {
		continue;
	}
	$s = $e['settings'] ?? array();
	ksort( $s );
	foreach ( $s as $k => $v ) {
		if ( preg_match( '/^_?(background|mask).*(image|video|slideshow|gallery|fallback)/', $k ) ) {
			continue;
		}
		printf( "  %-34s %s\n", $k, mb_strimwidth( is_scalar( $v ) ? (string) $v : wp_json_encode( $v ), 0, 150, '…' ) );
	}
	foreach ( $e['elements'] ?? array() as $c ) {
		printf( "  child %-8s %-14s %s\n", $c['id'], $c['widgetType'] ?? $c['elType'], $c['settings']['mf_input_name'] ?? '' );
	}
}
