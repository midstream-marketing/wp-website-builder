<?php
/**
 * Read-only: every widget on the given Elementor pages with its visible text settings
 * (titles, text, list items, accordion Q&A, buttons, images) - to rebuild a page in a new
 * design with its real content.
 *
 *   powershell -File bin/rwpphp.ps1 php/page-texts.php 608 1018 ...
 */

defined( 'ABSPATH' ) || exit;

$keys = array( 'title', 'sub_title', 'subtitle', 'bg_title', 'section_title', 'description', 'desc', 'editor', 'text', 'content', 'button_text', 'btn_text', 'link', 'shortcode', 'html', 'caption' );
$flat = function ( $v ): string {
	if ( is_array( $v ) ) {
		if ( isset( $v['url'] ) ) {
			return '[url ' . $v['url'] . ']';
		}
		return '';
	}
	return trim( preg_replace( '/\s+/', ' ', wp_strip_all_tags( (string) $v ) ) );
};
$walk = function ( array $els, int $d ) use ( &$walk, $keys, $flat ) {
	foreach ( $els as $e ) {
		$s   = $e['settings'] ?? array();
		$pad = str_repeat( '  ', $d );
		if ( 'widget' === ( $e['elType'] ?? '' ) ) {
			$out = array();
			foreach ( $s as $k => $v ) {
				if ( in_array( $k, $keys, true ) || preg_match( '/(title|text|desc|content|label|number|name)$/', $k ) ) {
					$t = $flat( $v );
					if ( '' !== $t ) {
						$out[] = "$k=" . mb_strimwidth( $t, 0, 400, '…' );
					}
				}
				if ( is_array( $v ) && isset( $v[0] ) && is_array( $v[0] ) ) { // repeaters (accordion, lists, counters)
					foreach ( $v as $i => $row ) {
						$r = array();
						foreach ( $row as $rk => $rv ) {
							$t = is_string( $rv ) || is_numeric( $rv ) ? $flat( $rv ) : ( isset( $rv['url'] ) ? '[url ' . $rv['url'] . ']' : '' );
							if ( '' !== $t && ! in_array( $rk, array( '_id' ), true ) && ! preg_match( '/color|size|icon|align|typography/', $rk ) ) {
								$r[] = "$rk=" . mb_strimwidth( $t, 0, 500, '…' );
							}
						}
						$out[] = "  [$k#$i] " . implode( ' | ', $r );
					}
				}
			}
			if ( ! empty( $s['image']['id'] ) ) {
				$out[] = 'image=#' . $s['image']['id'];
			}
			printf( "%s- %s\n%s    %s\n", $pad, $e['widgetType'] ?? '?', $pad, implode( "\n$pad    ", $out ) );
		} else {
			printf( "%s[%s%s]\n", $pad, $e['elType'] ?? '?', ! empty( $s['background_image']['id'] ) ? ' bg #' . $s['background_image']['id'] : '' );
		}
		$walk( $e['elements'] ?? array(), $d + 1 );
	}
};
foreach ( array_slice( $argv ?? array(), 1 ) as $id ) {
	$id   = (int) $id;
	$data = json_decode( (string) get_post_meta( $id, '_elementor_data', true ), true );
	printf( "\n==================== #%d %s /%s/ ====================\n", $id, get_the_title( $id ), get_post_field( 'post_name', $id ) );
	if ( is_array( $data ) ) {
		$walk( $data, 0 );
	} else {
		echo wp_strip_all_tags( get_post_field( 'post_content', $id ) ) . "\n";
	}
}
