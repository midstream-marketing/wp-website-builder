<?php
/** Read-only: settings of specific Elementor elements by id on a page. */
defined( 'ABSPATH' ) || exit;
$args = array_slice( $argv ?? array(), 1 );
$pid  = (int) array_shift( $args );
$want = array_flip( $args );
$data = json_decode( (string) get_post_meta( $pid, '_elementor_data', true ), true );
$walk = function ( array $els ) use ( &$walk, $want ) {
	foreach ( $els as $el ) {
		if ( isset( $want[ $el['id'] ?? '' ] ) ) {
			printf( "%s (%s):\n", $el['id'], $el['widgetType'] ?? $el['elType'] );
			foreach ( (array) ( $el['settings'] ?? array() ) as $k => $v ) {
				if ( preg_match( '/width|height|object|image|align|space/i', $k ) ) {
					printf( "   %-22s %s\n", $k, mb_strimwidth( is_array( $v ) ? wp_json_encode( $v ) : (string) $v, 0, 110 ) );
				}
			}
		}
		$walk( $el['elements'] ?? array() );
	}
};
$walk( is_array( $data ) ? $data : array() );
