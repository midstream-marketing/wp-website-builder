<?php
/**
 * Divi 5 layouts.
 *
 * Divi 5 stores a page as blocks (<!-- wp:divi/section {...} -->) with nested settings, where Divi 4 used
 * shortcodes. Divi 5 also ships its own converter from the Divi 4 form to the Divi 5 form, the one it uses
 * to migrate sites. So the same typed layout tree and the same checks as for Divi 4 are used here
 * (tools-divi.php): the layout is validated and written as Divi 4 shortcodes in memory, then handed to
 * Divi 5's converter, and only the Divi 5 blocks it returns are saved. Nothing in Divi 4 form reaches the page.
 *
 * Existing Divi 5 pages are read as an outline and edited by path. Elements an edit does not touch are kept
 * byte for byte.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

function wpu_bt_divi_is_v5() {
	return wpu_bt_has_divi() && ! wpu_bt_divi_is_v4();
}

/** Is this content in Divi 5 form? */
function wpu_bt_divi5_is_content( $content ) {
	return false !== strpos( (string) $content, '<!-- wp:divi/' );
}

/** Divi 5's own converter, or '' when this Divi version does not have it. */
function wpu_bt_divi5_converter() {
	$class = '\ET\Builder\Packages\Conversion\Conversion';
	return class_exists( $class ) && method_exists( $class, 'maybeConvertContent' ) ? $class : '';
}

/**
 * Divi 4 shortcodes (already validated, built by tools-divi.php) -> Divi 5 blocks.
 * @return string|WP_Error
 */
function wpu_bt_divi5_convert( $shortcode ) {
	$class = wpu_bt_divi5_converter();
	if ( '' === $class ) {
		return wpu_bt_err( 'This version of Divi 5 has no layout converter, so layouts cannot be built here. Update Divi.' );
	}
	// Each conversion is real work for Divi: bound it per request and per layout.
	static $runs = 0;
	if ( ++$runs > 90 ) {
		return wpu_bt_err( 'Too many layout conversions in one request. Send fewer operations at a time.' );
	}
	if ( strlen( (string) $shortcode ) > 2 * MB_IN_BYTES ) {
		return wpu_bt_err( 'The layout is larger than 2 MB.' );
	}
	// Divi's converter saves to Divi's own settings in two cases: the first time it runs on a site (it sets
	// up its colour list), and when a layout names a Divi global colour. Neither is allowed to happen here,
	// so a preview never writes anything.
	if ( function_exists( 'et_get_option' ) && false === et_get_option( 'et_global_data', false ) ) {
		return wpu_bt_err( 'Divi 5 has not finished its own first-time setup on this site. Open any page in the Divi builder once, then try again.' );
	}
	if ( false !== stripos( (string) $shortcode, 'gcid-' ) || false !== stripos( wpu_bt_divi_canon( $shortcode ), 'gcid-' ) ) {
		return wpu_bt_err( 'Divi global colours (gcid-...) are set in Divi itself. Send the colour as a value, for example #1a2b3c.' );
	}
	try {
		// Outside wp-admin Divi does not load its per-module conversion rules (to keep page loads fast).
		// This is the action Divi itself fires to load them before its builder converts a page.
		static $rules_loaded = false;
		if ( ! $rules_loaded ) {
			$rules_loaded = true;
			do_action( 'divi_visual_builder_before_d4_conversion' );
		}
		$out = call_user_func( array( $class, 'maybeConvertContent' ), (string) $shortcode );
		// Divi's extra pass that upgrades old Divi 4 content can leave a module unconverted in some request
		// types. This layout is freshly written in current form and does not need that pass.
		if ( ! is_string( $out ) || false !== strpos( $out, 'divi/shortcode-module' ) || false !== strpos( $out, '[et_pb_' ) ) {
			$out = call_user_func( array( $class, 'maybeConvertContent' ), (string) $shortcode, false );
		}
	} catch ( Throwable $e ) {
		return wpu_bt_err( 'Divi could not convert this layout to its Divi 5 form.' );
	}
	$out = is_string( $out ) ? trim( $out ) : '';
	// Divi may hand the result back already wrapped; the callers add the wrapper themselves.
	if ( preg_match( '/^<!-- wp:divi\/placeholder[^>]*? -->(.*)<!-- \/wp:divi\/placeholder -->$/s', $out, $m ) ) {
		$out = trim( $m[1] );
	}
	if ( '' === $out || 0 !== strpos( $out, '<!-- wp:divi/' ) || false !== strpos( $out, '[et_pb_' ) || false !== strpos( $out, 'divi/shortcode-module' ) || preg_match( '/\[\/?[a-z0-9_]+[^\]]*\]\s*$/', $out ) ) {
		return wpu_bt_err( 'Divi did not convert every part of this layout to its Divi 5 form, so nothing was saved. A module in it may not exist in Divi 5.' );
	}
	// The checks before this point were made on the Divi 4 form. Divi's converter decodes and reshapes
	// values, so what it produced is checked again here, on the form that will actually be stored.
	$doc = wpu_bt_divi5_parse( $out );
	if ( is_wp_error( $doc ) ) {
		return wpu_bt_err( 'Divi\'s converted layout could not be read back, so nothing was saved.' );
	}
	$bad = wpu_bt_divi5_check_nodes( $doc['nodes'] );
	if ( '' !== $bad ) {
		return wpu_bt_err( 'Not saved: after Divi converted it, ' . $bad . '.' );
	}
	return $out;
}

/** Exactly the token Divi writes for a plain global colour, and nothing else. */
function wpu_bt_divi5_is_colour_token( $leaf ) {
	if ( ! is_string( $leaf ) || ! preg_match( '/^\$variable\(\{"type":"color","value":\{"name":"(gcid-[a-z0-9-]{1,80})","settings":\{\}\}\}\)\$\z/', $leaf, $m ) ) {
		return false;
	}
	return '$variable(' . wp_json_encode( array( 'type' => 'color', 'value' => array( 'name' => $m[1], 'settings' => new stdClass() ) ) ) . ')$' === $leaf;
}

/** Why one stored text value is not acceptable in a Divi 5 block, or ''. */
function wpu_bt_divi5_leaf_reason( $leaf ) {
	// Also with tags, bracketed parts, entities and spaces taken out: Divi reads the text again after
	// shortcodes have run, so a token must not be assembled from pieces either.
	$flat = preg_replace( '/\s+/', '', html_entity_decode( preg_replace( '/\[[^\]]*\]/', '', wp_strip_all_tags( $leaf ) ), ENT_QUOTES | ENT_HTML5, 'UTF-8' ) );
	if ( false !== stripos( $leaf, '$variable(' ) || false !== stripos( $flat, '$variable(' ) || false !== stripos( wpu_bt_divi_canon( $leaf ), '$variable(' ) || false !== stripos( $leaf, '@ET-DC@' ) ) {
		return 'a setting holds Divi dynamic content, which is set in Divi itself';
	}
	if ( false !== strpos( $leaf, '[' ) || false !== stripos( $leaf, '&#' ) || false !== stripos( $leaf, '&lbr' ) || false !== strpos( $leaf, '%91' ) ) {
		if ( wpu_bt_divi_any_shortcode( $leaf ) ) {
			return 'a setting holds a shortcode';
		}
	}
	if ( preg_match( '/^(javascript|vbscript|livescript|data)\s*:/i', preg_replace( '/[\x00-\x20\x7f]+/', '', html_entity_decode( $leaf, ENT_QUOTES | ENT_HTML5, 'UTF-8' ) ) ) ) {
		return 'a setting holds a javascript: or data: address';
	}
	if ( false !== strpos( $leaf, '<' ) ) {
		$r = wpu_bt_guard_html_reason( $leaf );
		if ( '' !== $r ) {
			return 'a setting holds ' . $r;
		}
	}
	if ( false !== strpos( $leaf, '[' ) && wpu_bt_divi_has_tag( $leaf ) ) {
		return 'a setting holds a Divi shortcode';
	}
	return '';
}

/** Walk the settings of converted blocks. '' when clean. Code modules never come out of the converter here. */
function wpu_bt_divi5_check_nodes( array $nodes, $depth = 0 ) {
	foreach ( $nodes as $n ) {
		if ( in_array( $n['tag'], array( 'divi/code', 'divi/fullwidth-code', 'divi/shortcode-module', 'divi/svg', 'divi/global-layout' ), true ) ) {
			return 'it held a ' . $n['tag'] . ' element, which the bridge does not write';
		}
		if ( '' !== $n['json'] ) {
			$j = json_decode( $n['json'], true );
			if ( ! is_array( $j ) ) {
				return 'the settings of ' . $n['tag'] . ' were not valid';
			}
			$stack = array( $j );
			$seen  = 0;
			while ( $stack ) {
				$v = array_pop( $stack );
				if ( ++$seen > 20000 ) {
					return 'an element had too many settings to check';
				}
				if ( is_array( $v ) ) {
					foreach ( $v as $k => $c ) {
						$stack[] = $c;
						// Names inside settings are stored too.
						if ( is_string( $k ) && preg_match( '/[^A-Za-z0-9_.:-]/', $k ) ) {
							$r = wpu_bt_divi5_leaf_reason( $k );
							if ( '' !== $r || false !== strpos( $k, '<' ) ) {
								return '' !== $r ? $r : 'a setting name holds markup';
							}
						}
					}
				} elseif ( is_string( $v ) && '' !== $v ) {
					$r = wpu_bt_divi5_leaf_reason( $v );
					if ( '' !== $r ) {
						return $r;
					}
				}
			}
		}
		if ( $depth < 20 ) {
			$r = wpu_bt_divi5_check_nodes( $n['children'], $depth + 1 );
			if ( '' !== $r ) {
				return $r;
			}
		}
	}
	return '';
}

function wpu_bt_divi5_wrap( $blocks ) {
	return '<!-- wp:divi/placeholder -->' . $blocks . '<!-- /wp:divi/placeholder -->';
}

/* -------------------------------------------------------------------------
 * Page -> tree
 *
 * Node: array( 'tag' => 'divi/text', 'json' => raw settings text, 'raw_open', 'raw_close', 'void' => bool,
 * 'children' => nodes, 'attrs' => decoded lazily, 'changed' => bool ).
 * ---------------------------------------------------------------------- */

/** @return array|WP_Error array( 'nodes' => top-level nodes, 'wrapped' => bool ) */
function wpu_bt_divi5_parse( $content ) {
	$content = trim( (string) $content );
	// The same token pattern WordPress's block parser uses.
	if ( ! preg_match_all( '/<!--\s+(?P<closer>\/)?wp:(?P<namespace>[a-z][a-z0-9_-]*\/)?(?P<name>[a-z][a-z0-9_-]*)\s+(?P<attrs>{(?:(?:[^}]+|}+(?=})|(?!}\s+\/?-->).)*+)?}\s+)?(?P<void>\/)?-->/s', $content, $m, PREG_OFFSET_CAPTURE | PREG_SET_ORDER ) ) {
		return wpu_bt_err( 'This page has no Divi 5 layout.' );
	}
	$root  = array( 'tag' => '', 'children' => array() );
	$stack = array( &$root );
	$pos   = 0;
	foreach ( $m as $t ) {
		$start = $t[0][1];
		if ( '' !== trim( substr( $content, $pos, $start - $pos ) ) ) {
			return wpu_bt_err( 'This page has content outside its Divi layout, so it cannot be edited structurally without risk. Use builder_replace_text for text, or open and save it in Divi first.' );
		}
		$pos    = $start + strlen( $t[0][0] );
		$tag    = ( isset( $t['namespace'][0] ) && '' !== $t['namespace'][0] ? $t['namespace'][0] : 'core/' ) . $t['name'][0];
		$closer = isset( $t['closer'][0] ) && '/' === $t['closer'][0];
		$void   = isset( $t['void'][0] ) && '/' === $t['void'][0];
		$top    = &$stack[ count( $stack ) - 1 ];
		if ( 0 !== strpos( $tag, 'divi/' ) ) {
			return wpu_bt_err( 'This page mixes Divi with other blocks (' . sanitize_text_field( $tag ) . '), so it cannot be edited structurally here.' );
		}
		if ( $closer ) {
			if ( $top['tag'] !== $tag ) {
				return wpu_bt_err( 'This page\'s Divi layout is not well formed. Open and save it in Divi first.' );
			}
			$top['raw_close'] = $t[0][0];
			array_pop( $stack );
		} else {
			if ( count( $stack ) > 14 ) {
				return wpu_bt_err( 'This page nests Divi elements too deeply to edit here.' );
			}
			$top['children'][] = array( 'tag' => $tag, 'json' => isset( $t['attrs'][0] ) ? trim( $t['attrs'][0] ) : '', 'raw_open' => $t[0][0], 'raw_close' => '', 'void' => $void, 'children' => array(), 'changed' => false );
			if ( ! $void ) {
				$stack[] = &$top['children'][ count( $top['children'] ) - 1 ];
			}
		}
		unset( $top );
	}
	if ( 1 !== count( $stack ) || '' !== trim( substr( $content, $pos ) ) ) {
		return wpu_bt_err( 'This page\'s Divi layout has an element that is never closed, or content after it. Open and save it in Divi first.' );
	}
	$nodes   = $root['children'];
	$wrapped = 1 === count( $nodes ) && 'divi/placeholder' === $nodes[0]['tag'];
	return array( 'nodes' => $wrapped ? $nodes[0]['children'] : $nodes, 'wrapped' => $wrapped, 'open' => $wrapped ? $nodes[0]['raw_open'] : '', 'close' => $wrapped ? $nodes[0]['raw_close'] : '' );
}

/** Settings of a node as objects (so {} and [] stay what they were). */
function wpu_bt_divi5_attrs( array $node ) {
	if ( isset( $node['attrs'] ) ) {
		return $node['attrs'];
	}
	$j = '' === $node['json'] ? new stdClass() : json_decode( $node['json'] );
	return is_object( $j ) ? $j : new stdClass();
}

function wpu_bt_divi5_serialize_node( array $node ) {
	if ( empty( $node['changed'] ) ) {
		$open = $node['raw_open'];
	} else {
		// WordPress's own serialiser (it takes the object form, so {} stays {}).
		$attrs = wpu_bt_divi5_attrs( $node );
		$json  = get_object_vars( $attrs ) ? ' ' . serialize_block_attributes( $attrs ) : '';
		$open = '<!-- wp:' . $node['tag'] . $json . ( ! empty( $node['void'] ) ? ' /-->' : ' -->' );
	}
	if ( ! empty( $node['void'] ) ) {
		return $open;
	}
	$inner = '';
	foreach ( $node['children'] as $c ) {
		$inner .= wpu_bt_divi5_serialize_node( $c );
	}
	return $open . $inner . ( '' !== $node['raw_close'] ? $node['raw_close'] : '<!-- /wp:' . $node['tag'] . ' -->' );
}

function wpu_bt_divi5_serialize( array $doc ) {
	$out = '';
	foreach ( $doc['nodes'] as $n ) {
		$out .= wpu_bt_divi5_serialize_node( $n );
	}
	return $doc['wrapped'] ? $doc['open'] . $out . $doc['close'] : wpu_bt_divi5_wrap( $out );
}

/** Do the settings of every node read back as JSON? */
function wpu_bt_divi5_json_ok( array $nodes ) {
	foreach ( $nodes as $n ) {
		if ( ( '' !== $n['json'] && ! is_object( json_decode( $n['json'] ) ) ) || ! wpu_bt_divi5_json_ok( $n['children'] ) ) {
			return false;
		}
	}
	return true;
}

/** Read a.b.c from nested objects/arrays. */
function wpu_bt_divi5_dig( $v, $path ) {
	foreach ( explode( '.', $path ) as $k ) {
		if ( is_object( $v ) && isset( $v->$k ) ) {
			$v = $v->$k;
		} elseif ( is_array( $v ) && isset( $v[ $k ] ) ) {
			$v = $v[ $k ];
		} else {
			return null;
		}
	}
	return $v;
}

function wpu_bt_divi5_outline( array $nodes, $prefix = '', &$out = array() ) {
	foreach ( $nodes as $i => $n ) {
		if ( count( $out ) >= 500 ) {
			break;
		}
		$path = '' === $prefix ? (string) $i : $prefix . '.' . $i;
		$a    = wpu_bt_divi5_attrs( $n );
		$row  = array( 'path' => $path, 'type' => $n['tag'] );
		foreach ( array( 'admin_label' => 'module.meta.adminLabel.desktop.value', 'columns' => 'module.advanced.columnStructure.desktop.value', 'width' => 'module.advanced.type.desktop.value' ) as $label => $p ) {
			$v = wpu_bt_divi5_dig( $a, $p );
			if ( is_string( $v ) && '' !== $v ) {
				$row[ $label ] = substr( $v, 0, 120 );
			}
		}
		foreach ( array( 'title.innerContent.desktop.value.text', 'title.innerContent.desktop.value', 'button.innerContent.desktop.value.text', 'content.innerContent.desktop.value', 'name.innerContent.desktop.value' ) as $p ) {
			$v = wpu_bt_divi5_dig( $a, $p );
			if ( is_string( $v ) && '' !== trim( $v ) ) {
				$row['text'] = substr( trim( preg_replace( '/\s+/', ' ', html_entity_decode( wp_strip_all_tags( $v ), ENT_QUOTES | ENT_HTML5, 'UTF-8' ) ) ), 0, 140 );
				break;
			}
		}
		if ( $n['children'] ) {
			$row['children'] = count( $n['children'] );
		}
		$out[] = $row;
		wpu_bt_divi5_outline( $n['children'], $path, $out );
	}
	return $out;
}

/** Reference to the node at $path, or null. */
function &wpu_bt_divi5_ref( array &$nodes, $path ) {
	$null = null;
	$idx  = wpu_bt_parse_path( $path );
	if ( null === $idx || ! $idx ) {
		return $null;
	}
	$list = &$nodes;
	$last = count( $idx ) - 1;
	foreach ( $idx as $d => $i ) {
		if ( ! isset( $list[ $i ] ) ) {
			return $null;
		}
		if ( $d === $last ) {
			return $list[ $i ];
		}
		$list = &$list[ $i ]['children'];
	}
	return $null;
}

function wpu_bt_divi5_count( array $nodes ) {
	$n = count( $nodes );
	foreach ( $nodes as $c ) {
		$n += wpu_bt_divi5_count( $c['children'] );
	}
	return $n;
}

/** divi/accordion-item -> et_pb_accordion_item, when Divi 4 has that module. '' otherwise. */
function wpu_bt_divi5_d4_tag( $tag ) {
	$name = substr( (string) $tag, 5 );
	$map  = array( 'social-media-follow-item' => 'et_pb_social_media_follow_network', 'video-slider-item' => 'et_pb_video_slider_item', 'signup-custom-field' => 'et_pb_signup_custom_field', 'map-pin' => 'et_pb_map_pin' );
	$d4   = isset( $map[ $name ] ) ? $map[ $name ] : 'et_pb_' . str_replace( '-', '_', $name );
	if ( in_array( $d4, array( 'et_pb_section', 'et_pb_row', 'et_pb_column', 'et_pb_row_inner', 'et_pb_column_inner' ), true ) ) {
		return $d4;
	}
	return wpu_bt_divi_info( $d4 ) ? $d4 : '';
}

/** Does this element or anything in it fall outside what may be written (Code modules, add-on modules)? */
function wpu_bt_divi5_tree_refused( array $node ) {
	$d4 = wpu_bt_divi5_d4_tag( $node['tag'] );
	if ( '' === $d4 || is_wp_error( wpu_bt_divi_writable( $d4 ) ) ) {
		return true;
	}
	foreach ( $node['children'] as $c ) {
		if ( wpu_bt_divi5_tree_refused( $c ) ) {
			return true;
		}
	}
	return false;
}

/** Does any setting hold Divi dynamic content (any $variable token that is not a plain global colour)? */
function wpu_bt_divi5_has_dynamic( $v, $depth = 0 ) {
	if ( is_string( $v ) ) {
		return false !== stripos( $v, '$variable(' ) && ! wpu_bt_divi5_is_colour_token( $v );
	}
	if ( $depth > 30 || ! ( is_object( $v ) || is_array( $v ) ) ) {
		return false;
	}
	foreach ( (array) $v as $c ) {
		if ( wpu_bt_divi5_has_dynamic( $c, $depth + 1 ) ) {
			return true;
		}
	}
	return false;
}

/** Settings Divi's converter writes for a bare element of this kind (cached per request). */
function wpu_bt_divi5_baseline( $d4_tag, $d5_tag ) {
	static $cache = array();
	if ( isset( $cache[ $d4_tag ] ) ) {
		return $cache[ $d4_tag ];
	}
	$conv = wpu_bt_divi5_nodes_from_d4( array( 'tag' => $d4_tag, 'attrs' => array(), 'children' => array(), 'content' => '' ) );
	if ( is_wp_error( $conv ) ) {
		return $conv;
	}
	return $cache[ $d4_tag ] = 1 === count( $conv ) && $conv[0]['tag'] === $d5_tag ? wpu_bt_divi5_attrs( $conv[0] ) : new stdClass();
}

/** What $with holds that $base does not (or holds differently). Null when nothing. */
function wpu_bt_divi5_diff( $with, $base ) {
	if ( is_object( $with ) && is_object( $base ) ) {
		$out = new stdClass();
		foreach ( get_object_vars( $with ) as $k => $v ) {
			if ( ! property_exists( $base, $k ) ) {
				$out->$k = $v;
				continue;
			}
			$d = wpu_bt_divi5_diff( $v, $base->$k );
			if ( null !== $d ) {
				$out->$k = $d;
			}
		}
		return get_object_vars( $out ) ? $out : null;
	}
	return wp_json_encode( $with ) === wp_json_encode( $base ) ? null : $with;
}

/** Dotted names of every value in a settings object. */
function wpu_bt_divi5_paths( $v, $prefix = '', $depth = 0 ) {
	if ( ! is_object( $v ) || $depth > 30 ) {
		return '' === $prefix ? array() : array( $prefix );
	}
	$out = array();
	foreach ( get_object_vars( $v ) as $k => $c ) {
		$out = array_merge( $out, wpu_bt_divi5_paths( $c, '' === $prefix ? (string) $k : $prefix . '.' . $k, $depth + 1 ) );
	}
	return $out;
}

/** Does this element, or anything in it, use Divi dynamic content? */
function wpu_bt_divi5_tree_dynamic( array $node, $depth = 0 ) {
	if ( wpu_bt_divi5_has_dynamic( wpu_bt_divi5_attrs( $node ) ) ) {
		return true;
	}
	foreach ( $node['children'] as $c ) {
		if ( $depth > 30 || wpu_bt_divi5_tree_dynamic( $c, $depth + 1 ) ) {
			return true;
		}
	}
	return false;
}

/** A full copy of a node, so a duplicate never shares settings with its original. */
function wpu_bt_divi5_clone( array $node ) {
	if ( isset( $node['attrs'] ) ) {
		$node['attrs'] = json_decode( wp_json_encode( $node['attrs'] ) );
	}
	foreach ( $node['children'] as $i => $c ) {
		$node['children'][ $i ] = wpu_bt_divi5_clone( $c );
	}
	return $node;
}

/** Merge new settings into existing ones: objects merge key by key, everything else is replaced. */
function wpu_bt_divi5_merge( $base, $add ) {
	if ( ! is_object( $base ) || ! is_object( $add ) ) {
		return $add;
	}
	foreach ( get_object_vars( $add ) as $k => $v ) {
		$base->$k = isset( $base->$k ) ? wpu_bt_divi5_merge( $base->$k, $v ) : $v;
	}
	return $base;
}

/**
 * Turn a validated Divi 4 node (from tools-divi.php) into Divi 5 nodes through Divi's converter.
 * @return array|WP_Error list of nodes
 */
function wpu_bt_divi5_nodes_from_d4( array $d4_node ) {
	$blocks = wpu_bt_divi5_convert( wpu_bt_divi_serialize( $d4_node ) );
	if ( is_wp_error( $blocks ) ) {
		return $blocks;
	}
	$doc = wpu_bt_divi5_parse( $blocks );
	if ( is_wp_error( $doc ) ) {
		return $doc;
	}
	return $doc['nodes'];
}

/** The Divi 4 "parent" that stands for a Divi 5 node, so the Divi 4 placement rules can be reused. */
function wpu_bt_divi5_parent_as_d4( $node ) {
	if ( null === $node ) {
		return null;
	}
	$d4 = wpu_bt_divi5_d4_tag( $node['tag'] );
	if ( '' === $d4 ) {
		return wpu_bt_err( $node['tag'] . ' is not an element the bridge places items into.' );
	}
	$attrs = array();
	if ( 'et_pb_section' === $d4 ) {
		$type = wpu_bt_divi5_dig( wpu_bt_divi5_attrs( $node ), 'module.advanced.type.desktop.value' );
		if ( 'fullwidth' === $type ) {
			$attrs['fullwidth'] = 'on';
		} elseif ( 'specialty' === $type ) {
			$attrs['specialty'] = 'on';
		}
	}
	return array( 'tag' => $d4, 'attrs' => $attrs, 'children' => array(), 'content' => '' );
}

/**
 * divi_page_edit for a page in Divi 5 form.
 * @return array|WP_Error
 */
function wpu_bt_divi5_edit( WP_Post $p, array $a ) {
	$id  = (int) $p->ID;
	$doc = wpu_bt_divi5_parse( $p->post_content );
	if ( is_wp_error( $doc ) ) {
		return $doc;
	}
	if ( wpu_bt_divi5_serialize( $doc ) !== trim( $p->post_content ) ) {
		return wpu_bt_err( 'This page\'s Divi layout is stored in a form that cannot be rewritten exactly, so it is not edited here. Open and save it in Divi first.' );
	}
	if ( ! wpu_bt_divi5_json_ok( $doc['nodes'] ) ) {
		return wpu_bt_err( 'An element on this page has settings that cannot be read, so the page is not edited here. Open and save it in Divi first.' );
	}
	$ops = (array) $a['operations'];
	if ( ! $ops || count( $ops ) > 40 ) {
		return wpu_bt_err( 'Send 1 to 40 operations.' );
	}
	$tree     = &$doc['nodes'];
	$warnings = array();
	$log      = array();
	$bytes    = strlen( $p->post_content );
	foreach ( $ops as $n => $op ) {
		$op   = (array) $op;
		$kind = isset( $op['op'] ) ? (string) $op['op'] : '';
		$fail = function ( $msg ) use ( $n ) {
			return wpu_bt_err( 'Operation ' . $n . ': ' . $msg );
		};
		if ( 'insert' === $kind ) {
			$ppath  = isset( $op['parent'] ) ? (string) $op['parent'] : '';
			$parent = null;
			if ( '' !== $ppath ) {
				$parent = &wpu_bt_divi5_ref( $tree, $ppath );
				if ( null === $parent ) {
					return $fail( 'no element at parent path ' . sanitize_text_field( $ppath ) . '.' );
				}
			}
			$as_d4 = wpu_bt_divi5_parent_as_d4( $parent );
			if ( is_wp_error( $as_d4 ) ) {
				return $fail( $as_d4->get_error_message() );
			}
			$d4 = wpu_bt_divi_node_for( $as_d4, isset( $op['node'] ) ? $op['node'] : array(), $warnings );
			if ( is_wp_error( $d4 ) ) {
				return $fail( $d4->get_error_message() );
			}
			$new = wpu_bt_divi5_nodes_from_d4( $d4 );
			if ( is_wp_error( $new ) ) {
				return $fail( $new->get_error_message() );
			}
			if ( null === $parent ) {
				$list = &$tree;
			} else {
				if ( ! empty( $parent['void'] ) ) {
					$parent['void']    = false;
					$parent['changed'] = true;
					$parent['attrs']   = wpu_bt_divi5_attrs( $parent );
				}
				$list = &$parent['children'];
			}
			$at = isset( $op['index'] ) ? max( 0, min( count( $list ), (int) $op['index'] ) ) : count( $list );
			array_splice( $list, $at, 0, $new );
			$log[] = array( 'op' => $n, 'inserted' => $new ? $new[0]['tag'] : '', 'at' => ( '' === $ppath ? '' : $ppath . '.' ) . $at );
			unset( $list, $parent );
			continue;
		}
		$path = isset( $op['path'] ) ? (string) $op['path'] : '';
		$node = &wpu_bt_divi5_ref( $tree, $path );
		if ( null === $node ) {
			return $fail( 'no element at path ' . sanitize_text_field( $path ) . '.' );
		}
		$cut   = strrpos( $path, '.' );
		$ppath = false === $cut ? '' : substr( $path, 0, $cut );
		$idx   = (int) ( false === $cut ? $path : substr( $path, $cut + 1 ) );
		if ( 'set_attrs' === $kind || 'set_content' === $kind ) {
			$d4 = wpu_bt_divi5_d4_tag( $node['tag'] );
			if ( '' === $d4 ) {
				return $fail( $node['tag'] . ' has no settings the bridge can write. Change it in Divi.' );
			}
			$can = wpu_bt_divi_writable( $d4 );
			if ( is_wp_error( $can ) ) {
				return $fail( $can->get_error_message() );
			}
			$cur = wpu_bt_divi5_attrs( $node );
			if ( wpu_bt_divi5_has_dynamic( $cur ) ) {
				return $fail( 'this element uses Divi dynamic content, so it is changed in Divi.' );
			}
			$frag = array( 'tag' => $d4, 'attrs' => array(), 'children' => array(), 'content' => '' );
			if ( 'set_attrs' === $kind ) {
				$send = array();
				foreach ( isset( $op['attrs'] ) ? (array) $op['attrs'] : array() as $k => $v ) {
					$k = (string) $k;
					if ( in_array( $k, array( 'type', 'column_structure', 'fullwidth', 'specialty', 'fb_built', 'global_module', 'global_parent' ), true ) ) {
						return $fail( 'setting "' . $k . '" is structural; replace the element instead.' );
					}
					if ( null === $v ) {
						return $fail( 'on Divi 5 a setting cannot be removed by name; set the value you want instead (for example an empty text).' );
					}
					$send[ $k ] = $v;
				}
				$clean = wpu_bt_divi_attrs( $d4, $send, $warnings );
				if ( is_wp_error( $clean ) ) {
					return $fail( $clean->get_error_message() );
				}
				if ( ! $clean ) {
					$log[] = array( 'op' => $n, 'set_attrs' => $path, 'changed' => 0 );
					unset( $node );
					continue;
				}
				$frag['attrs'] = $clean;
			} else {
				$info = wpu_bt_divi_info( $d4 );
				if ( ! $info || 'structure' === $info['kind'] || '' !== $info['child'] || $node['children'] ) {
					return $fail( $node['tag'] . ' holds other elements, not content.' );
				}
				$c = wpu_bt_divi_content( isset( $op['content'] ) ? $op['content'] : '', $d4 );
				if ( is_wp_error( $c ) ) {
					return $fail( $c->get_error_message() );
				}
				$frag['content'] = $c;
			}
			$conv = wpu_bt_divi5_nodes_from_d4( $frag );
			if ( is_wp_error( $conv ) ) {
				return $fail( $conv->get_error_message() );
			}
			if ( 1 !== count( $conv ) || $conv[0]['tag'] !== $node['tag'] ) {
				return $fail( 'Divi converted this setting into a different element, so it is not applied here.' );
			}
			// Divi's converter also writes defaults of its own (block layout on rows, text alignment on
			// sliders ...). Only what this change adds, compared with converting the bare element, is applied.
			$base = wpu_bt_divi5_baseline( $d4, $node['tag'] );
			if ( is_wp_error( $base ) ) {
				return $fail( $base->get_error_message() );
			}
			$add = wpu_bt_divi5_diff( wpu_bt_divi5_attrs( $conv[0] ), $base );
			if ( null === $add ) {
				$add = new stdClass();
			}
			unset( $add->builderVersion );
			if ( 'set_content' === $kind && ! isset( $add->content ) ) {
				$add->content = json_decode( wp_json_encode( array( 'innerContent' => array( 'desktop' => array( 'value' => '' ) ) ) ) );
			}
			// Divi decides what a Divi setting means (one setting can touch several stored values), so the
			// result lists every stored value this operation set.
			$set = wpu_bt_divi5_paths( $add );
			if ( ! $set ) {
				$log[] = array( 'op' => $n, $kind => $path, 'changed' => 0, 'note' => 'Divi stores nothing for this value (it equals Divi\'s default), so nothing was changed.' );
				unset( $node );
				continue;
			}
			$node['attrs']   = wpu_bt_divi5_merge( $cur, $add );
			$node['changed'] = true;
			$log[]           = array( 'op' => $n, $kind => $path, 'changed' => count( $set ), 'stored_values_set' => array_slice( $set, 0, 40 ) );
		} elseif ( in_array( $kind, array( 'remove', 'duplicate', 'move', 'replace' ), true ) ) {
			unset( $node );
			$par = null;
			if ( '' === $ppath ) {
				$list = &$tree;
			} else {
				$par = &wpu_bt_divi5_ref( $tree, $ppath );
				if ( in_array( $par['tag'], array( 'divi/row', 'divi/row-inner' ), true ) ) {
					return $fail( 'columns cannot be removed, moved or duplicated one by one. Replace the row to change its columns.' );
				}
				if ( 'divi/section' === $par['tag'] && 'specialty' === wpu_bt_divi5_dig( wpu_bt_divi5_attrs( $par ), 'module.advanced.type.desktop.value' ) ) {
					return $fail( 'the columns of a specialty section are changed in Divi.' );
				}
				$list = &$par['children'];
			}
			if ( 'duplicate' === $kind ) {
				$bytes += strlen( wpu_bt_divi5_serialize_node( $list[ $idx ] ) );
				if ( $bytes > 2 * MB_IN_BYTES ) {
					return $fail( 'the page would be larger than 2 MB.' );
				}
				if ( wpu_bt_divi5_tree_refused( $list[ $idx ] ) ) {
					return $fail( 'this element holds a module the bridge does not write (a Code module or one from another plugin), so it is not copied.' );
				}
				if ( wpu_bt_divi5_tree_dynamic( $list[ $idx ] ) ) {
					return $fail( 'this element uses Divi dynamic content, so it is copied in Divi.' );
				}
				array_splice( $list, $idx + 1, 0, array( wpu_bt_divi5_clone( $list[ $idx ] ) ) );
			} elseif ( 'remove' === $kind ) {
				array_splice( $list, $idx, 1 );
			} elseif ( 'move' === $kind ) {
				$to   = isset( $op['index'] ) ? max( 0, min( count( $list ) - 1, (int) $op['index'] ) ) : 0;
				$item = array_splice( $list, $idx, 1 );
				array_splice( $list, $to, 0, $item );
			} else {
				$as_d4 = wpu_bt_divi5_parent_as_d4( $par );
				if ( is_wp_error( $as_d4 ) ) {
					return $fail( $as_d4->get_error_message() );
				}
				$d4 = wpu_bt_divi_node_for( $as_d4, isset( $op['node'] ) ? $op['node'] : array(), $warnings );
				if ( is_wp_error( $d4 ) ) {
					return $fail( $d4->get_error_message() );
				}
				$new = wpu_bt_divi5_nodes_from_d4( $d4 );
				if ( is_wp_error( $new ) ) {
					return $fail( $new->get_error_message() );
				}
				array_splice( $list, $idx, 1, $new );
			}
			$log[] = array( 'op' => $n, $kind => $path );
			unset( $list, $par );
			if ( wpu_bt_divi5_count( $tree ) > 4000 ) {
				return $fail( 'the page would have more than 4000 elements.' );
			}
		} else {
			return $fail( 'unknown op "' . sanitize_text_field( $kind ) . '". Use set_attrs, set_content, insert, replace, remove, duplicate or move.' );
		}
		unset( $node );
	}
	unset( $tree );
	$new = wpu_bt_divi5_serialize( $doc );
	if ( strlen( $new ) > 2 * MB_IN_BYTES || wpu_bt_divi5_count( $doc['nodes'] ) > 4000 ) {
		return wpu_bt_err( 'The page would be larger than 2 MB or 4000 elements.' );
	}
	// What is about to be saved must read back as a clean Divi 5 layout.
	$back = wpu_bt_divi5_parse( $new );
	if ( is_wp_error( $back ) || ! wpu_bt_divi5_json_ok( $back['nodes'] ) || false !== strpos( $new, '[et_pb_' ) ) {
		return wpu_bt_err( 'The edited layout did not come out as a clean Divi 5 layout, so nothing was saved.' );
	}
	$warnings = array_values( array_unique( $warnings ) );
	if ( wpu_bt_bool( $a, 'dry_run' ) ) {
		return array( 'dry_run' => true, 'divi' => 5, 'operations' => $log, 'warnings' => $warnings, 'elements' => wpu_bt_divi5_outline( $doc['nodes'] ) );
	}
	if ( $new === trim( $p->post_content ) ) {
		return array( 'id' => $id, 'changed' => false, 'operations' => $log );
	}
	$undo = wpu_bt_divi_undo_items( $id );
	$r    = wpu_bt_divi_save( $id, $new, false );
	if ( is_wp_error( $r ) ) {
		return $r;
	}
	$cid = wpu_bt_change_add( 'divi_page_edit', 'Edited Divi 5 layout on #' . $id . ' "' . get_the_title( $id ) . '" (' . count( $log ) . ' operations)', array( 'kind' => 'multi', 'items' => $undo ) );
	return array( 'id' => $id, 'divi' => 5, 'operations' => $log, 'warnings' => $warnings, 'url' => get_permalink( $id ), 'preview' => get_preview_post_link( $id ), 'change_id' => $cid );
}
