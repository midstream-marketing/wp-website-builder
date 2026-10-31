<?php
/**
 * Read-only outline of Elementor templates: widget tree (type + visible text),
 * image URLs, links and nav menus each template uses.
 *
 *   powershell -File bin/rwpphp.ps1 php/template-dump.php
 *   powershell -File bin/rwpphp.ps1 php/template-dump.php 629 14 602
 *   (IDs as arguments; without any, the defaults below)
 */

defined( 'ABSPATH' ) || exit;

$ids = array_values( array_filter( array_map( 'intval', array_slice( $argv ?? array(), 1 ) ) ) );
if ( ! $ids ) {
	$ids = array( 23, 14, 17, 20, 26 );
}

function wpsb_text( array $s ): string {
	foreach ( array( 'title', 'editor', 'text', 'description_text', 'title_text', 'button_text', 'tab_title', 'heading' ) as $k ) {
		if ( ! empty( $s[ $k ] ) && is_string( $s[ $k ] ) ) {
			return mb_strimwidth( trim( preg_replace( '/\s+/', ' ', wp_strip_all_tags( $s[ $k ] ) ) ), 0, 90, '…' );
		}
	}
	return '';
}

function wpsb_walk( array $els, int $depth, array &$imgs, array &$links, array &$menus ): void {
	foreach ( $els as $el ) {
		$s    = (array) ( $el['settings'] ?? array() );
		$type = $el['widgetType'] ?? $el['elType'] ?? '?';
		array_walk_recursive( $s, function ( $v, $k ) use ( &$imgs, &$links ) {
			if ( ! is_string( $v ) ) {
				return;
			}
			if ( $k === 'url' && preg_match( '/\.(jpe?g|png|webp|gif|svg|avif)(\?|$)/i', $v ) ) {
				$imgs[ $v ] = true;
			} elseif ( $k === 'url' && $v !== '' ) {
				$links[ $v ] = true;
			}
		} );
		if ( ! empty( $s['menu'] ) ) {
			$menus[ (string) $s['menu'] ] = true;
		}
		if ( $type !== 'container' && $type !== 'section' && $type !== 'column' ) {
			printf( "%s%s  %s\n", str_repeat( '  ', $depth ), $type, wpsb_text( $s ) );
		} elseif ( $depth < 2 ) {
			printf( "%s[%s]\n", str_repeat( '  ', $depth ), $type );
		}
		wpsb_walk( (array) ( $el['elements'] ?? array() ), $depth + 1, $imgs, $links, $menus );
	}
}

foreach ( $ids as $id ) {
	echo "\n" . str_repeat( '=', 74 ) . "\n  #$id " . get_the_title( $id ) . "\n" . str_repeat( '=', 74 ) . "\n";
	$data = json_decode( (string) get_post_meta( $id, '_elementor_data', true ), true );
	if ( ! is_array( $data ) ) {
		echo "  (no elementor data)\n";
		continue;
	}
	$imgs = $links = $menus = array();
	wpsb_walk( $data, 0, $imgs, $links, $menus );
	echo "\n  images: " . count( $imgs ) . "\n";
	foreach ( array_keys( $imgs ) as $u ) {
		echo "    $u\n";
	}
	echo "  links:\n";
	foreach ( array_keys( $links ) as $u ) {
		echo "    $u\n";
	}
	if ( $menus ) {
		echo '  nav menus: ' . implode( ', ', array_keys( $menus ) ) . "\n";
	}
}

echo "\n" . str_repeat( '=', 74 ) . "\n  MENUS\n" . str_repeat( '=', 74 ) . "\n";
foreach ( wp_get_nav_menus() as $m ) {
	printf( "  %-6d %-20s slug=%s items=%d\n", $m->term_id, $m->name, $m->slug, $m->count );
	foreach ( (array) wp_get_nav_menu_items( $m->term_id ) as $it ) {
		printf( "         - %-20s %s\n", $it->title, $it->url );
	}
}
