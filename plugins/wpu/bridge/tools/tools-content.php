<?php
/**
 * Content tools: posts, pages and custom post types; Gutenberg blocks; design tokens; media; terms.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** Post types these tools may create or edit. Templates, orders and Elementor's library are left alone. */
function wpu_bt_editable_type( $type ) {
	$pt = get_post_type_object( (string) $type );
	if ( ! $pt || ! $pt->show_ui ) {
		return false;
	}
	return ! in_array( $pt->name, array( 'product', 'product_variation', 'attachment', 'wp_template', 'wp_template_part', 'wp_global_styles', 'wp_navigation', 'wp_font_family', 'wp_font_face', 'elementor_library', 'shop_order', 'shop_order_placehold', 'shop_coupon', 'shop_order_refund', 'acf-field-group', 'acf-field', 'acf-post-type', 'acf-taxonomy' ), true );
}

/** wp_kses_post plus a block check. Returns array( content, warnings ). */
function wpu_bt_clean_content( $content ) {
	$content  = wp_kses_post( (string) $content );
	$warnings = wpu_bt_validate_blocks( $content );
	return array( $content, $warnings );
}

/** Unknown block names, unbalanced delimiters and loose HTML between blocks. */
function wpu_bt_validate_blocks( $content ) {
	$warnings = array();
	if ( false === strpos( $content, '<!-- wp:' ) ) {
		return $warnings;
	}
	preg_match_all( '/<!--\s+wp:([a-z0-9\/-]+)(?:\s+(\{.*?\}))?\s+(\/)?-->/s', $content, $open, PREG_SET_ORDER );
	preg_match_all( '/<!--\s+\/wp:([a-z0-9\/-]+)\s+-->/', $content, $close );
	$opens = 0;
	foreach ( $open as $m ) {
		if ( empty( $m[3] ) ) {
			$opens++;
		}
		if ( ! empty( $m[2] ) && null === json_decode( $m[2] ) ) {
			$warnings[] = 'Block ' . $m[1] . ' has attributes that are not valid JSON: ' . substr( $m[2], 0, 80 );
		}
	}
	if ( $opens !== count( $close[1] ) ) {
		$warnings[] = 'Block comments are unbalanced: ' . $opens . ' opening and ' . count( $close[1] ) . ' closing. The editor will show broken blocks.';
	}
	$reg     = WP_Block_Type_Registry::get_instance();
	$unknown = array();
	$walk    = function ( $blocks ) use ( &$walk, $reg, &$unknown ) {
		foreach ( $blocks as $b ) {
			if ( ! empty( $b['blockName'] ) && ! $reg->is_registered( $b['blockName'] ) ) {
				$unknown[ $b['blockName'] ] = true;
			}
			if ( ! empty( $b['innerBlocks'] ) ) {
				$walk( $b['innerBlocks'] );
			}
		}
	};
	$blocks = parse_blocks( $content );
	$walk( $blocks );
	if ( $unknown ) {
		$warnings[] = 'Blocks not registered on this site (they show as "unsupported"): ' . implode( ', ', array_keys( $unknown ) );
	}
	foreach ( $blocks as $b ) {
		if ( empty( $b['blockName'] ) && '' !== trim( (string) $b['innerHTML'] ) ) {
			$warnings[] = 'Some HTML sits outside any block and will become a Classic block: "' . substr( trim( wp_strip_all_tags( $b['innerHTML'] ) ), 0, 60 ) . '"';
			break;
		}
	}
	return $warnings;
}

/* -------------------------------------------------------------------------
 * Block tree helpers. Paths are "2" (third top-level block) or "2.0.1" (into innerBlocks).
 * Whitespace between top-level blocks is not counted.
 * ---------------------------------------------------------------------- */

function wpu_bt_block_visible( $b ) {
	return ! empty( $b['blockName'] ) || '' !== trim( (string) $b['innerHTML'] );
}

/** Flat outline of a block tree for reading. */
function wpu_bt_block_outline( array $blocks, $prefix = '', &$out = array() ) {
	$i = 0;
	foreach ( $blocks as $b ) {
		if ( '' === $prefix && ! wpu_bt_block_visible( $b ) ) {
			continue;
		}
		if ( count( $out ) >= 400 ) {
			break;
		}
		$path  = '' === $prefix ? (string) $i : $prefix . '.' . $i;
		$attrs = $b['attrs'] ? wp_json_encode( $b['attrs'], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE ) : '';
		$out[] = array(
			'path'  => $path,
			'block' => $b['blockName'] ? $b['blockName'] : 'core/freeform',
			'attrs' => strlen( $attrs ) > 300 ? substr( $attrs, 0, 300 ) . '...' : $attrs,
			'text'  => substr( trim( preg_replace( '/\s+/', ' ', wp_strip_all_tags( (string) $b['innerHTML'] ) ) ), 0, 140 ),
			'inner' => count( $b['innerBlocks'] ),
		);
		if ( $b['innerBlocks'] ) {
			wpu_bt_block_outline( $b['innerBlocks'], $path, $out );
		}
		$i++;
	}
	return $out;
}

/** Top-level raw index of the n-th visible block, or -1. */
function wpu_bt_block_raw_index( array $blocks, $n ) {
	$v = 0;
	foreach ( $blocks as $raw => $b ) {
		if ( ! wpu_bt_block_visible( $b ) ) {
			continue;
		}
		if ( $v === $n ) {
			return $raw;
		}
		$v++;
	}
	return -1;
}

function wpu_bt_parse_path( $path ) {
	$path = trim( (string) $path );
	if ( ! preg_match( '/^\d+(\.\d+){0,9}$/', $path ) ) {
		return null;
	}
	return array_map( 'intval', explode( '.', $path ) );
}

function wpu_bt_ws_block() {
	return array( 'blockName' => null, 'attrs' => array(), 'innerBlocks' => array(), 'innerHTML' => "\n\n", 'innerContent' => array( "\n\n" ) );
}

/** Named blocks parsed from markup (whitespace dropped). */
function wpu_bt_markup_blocks( $markup ) {
	$out = array();
	foreach ( parse_blocks( (string) $markup ) as $b ) {
		if ( wpu_bt_block_visible( $b ) ) {
			$out[] = $b;
		}
	}
	return $out;
}

/**
 * Splice children of a container block: remove $remove children at $at and insert $new there,
 * keeping innerContent's placeholders (one null per inner block) in step.
 */
function wpu_bt_splice_inner( array &$parent, $at, $remove, array $new ) {
	$count = count( $parent['innerBlocks'] );
	$at    = max( 0, min( $at, $count ) );
	// Positions of the nulls in innerContent.
	$nulls = array();
	foreach ( $parent['innerContent'] as $k => $piece ) {
		if ( null === $piece ) {
			$nulls[] = $k;
		}
	}
	$ic = $parent['innerContent'];
	// Remove placeholders from the end so earlier offsets stay right.
	for ( $r = $remove - 1; $r >= 0; $r-- ) {
		if ( isset( $nulls[ $at + $r ] ) ) {
			array_splice( $ic, $nulls[ $at + $r ], 1 );
		}
	}
	// Where to insert the new placeholders.
	$nulls = array();
	foreach ( $ic as $k => $piece ) {
		if ( null === $piece ) {
			$nulls[] = $k;
		}
	}
	if ( isset( $nulls[ $at ] ) ) {
		$pos = $nulls[ $at ];
	} elseif ( $nulls ) {
		$pos = end( $nulls ) + 1;
	} else {
		// Empty container: before its closing markup if it has opening and closing parts.
		$pos = count( $ic ) >= 2 ? count( $ic ) - 1 : count( $ic );
	}
	$ins = array();
	foreach ( $new as $unused ) {
		$ins[] = null;
	}
	array_splice( $ic, $pos, 0, $ins );
	$parent['innerContent'] = $ic;
	array_splice( $parent['innerBlocks'], $at, $remove, $new );
}

/**
 * Apply one structural operation to the tree. $path addresses an existing block.
 * $mode: 'replace' | 'remove' | 'before' | 'after'
 */
function wpu_bt_tree_op( array &$blocks, array $path, $mode, array $new ) {
	if ( 1 === count( $path ) ) {
		$raw = wpu_bt_block_raw_index( $blocks, $path[0] );
		if ( $raw < 0 ) {
			return wpu_bt_err( 'No top-level block at path ' . $path[0] . '.' );
		}
		$with_ws = array();
		foreach ( $new as $i => $b ) {
			if ( $i > 0 ) {
				$with_ws[] = wpu_bt_ws_block();
			}
			$with_ws[] = $b;
		}
		if ( 'replace' === $mode ) {
			array_splice( $blocks, $raw, 1, $with_ws );
		} elseif ( 'remove' === $mode ) {
			array_splice( $blocks, $raw, 1 );
		} elseif ( 'before' === $mode ) {
			array_splice( $blocks, $raw, 0, array_merge( $with_ws, array( wpu_bt_ws_block() ) ) );
		} else {
			array_splice( $blocks, $raw + 1, 0, array_merge( array( wpu_bt_ws_block() ), $with_ws ) );
		}
		return true;
	}
	$raw = wpu_bt_block_raw_index( $blocks, $path[0] );
	if ( $raw < 0 ) {
		return wpu_bt_err( 'No top-level block at path ' . $path[0] . '.' );
	}
	$parent = &$blocks[ $raw ];
	for ( $d = 1; $d < count( $path ) - 1; $d++ ) {
		if ( ! isset( $parent['innerBlocks'][ $path[ $d ] ] ) ) {
			return wpu_bt_err( 'No block at path ' . implode( '.', array_slice( $path, 0, $d + 1 ) ) . '.' );
		}
		$parent = &$parent['innerBlocks'][ $path[ $d ] ];
	}
	$last = end( $path );
	if ( ! isset( $parent['innerBlocks'][ $last ] ) ) {
		return wpu_bt_err( 'No block at path ' . implode( '.', $path ) . '.' );
	}
	if ( 'replace' === $mode ) {
		wpu_bt_splice_inner( $parent, $last, 1, $new );
	} elseif ( 'remove' === $mode ) {
		wpu_bt_splice_inner( $parent, $last, 1, array() );
	} elseif ( 'before' === $mode ) {
		wpu_bt_splice_inner( $parent, $last, 0, $new );
	} else {
		wpu_bt_splice_inner( $parent, $last + 1, 0, $new );
	}
	return true;
}

/**
 * Replace visible text only: never inside block comment delimiters (block attributes), other HTML
 * comments, or HTML tags (class names, links, image sources), so blocks stay valid in the editor.
 */
function wpu_bt_replace_outside_comments( $content, $find, $replace, $limit, $case = true ) {
	$parts = wpu_bt_split_markup( $content );
	$done  = 0;
	foreach ( $parts as $i => $part ) {
		if ( 1 === $i % 2 || '' === $part ) {
			continue; // a block delimiter
		}
		$pattern = '/' . preg_quote( $find, '/' ) . '/' . ( $case ? '' : 'i' ) . 'u';
		$left    = $limit - $done;
		if ( $left <= 0 ) {
			break;
		}
		$n   = 0;
		$new = preg_replace( $pattern, str_replace( array( '\\', '$' ), array( '\\\\', '\\$' ), $replace ), $part, $left, $n );
		if ( null === $new ) {
			continue; // not valid UTF-8: leave this part alone rather than lose it
		}
		$parts[ $i ] = $new;
		$done       += $n;
	}
	return array( implode( '', $parts ), $done );
}

/* -------------------------------------------------------------------------
 * Shared pieces for create/update
 * ---------------------------------------------------------------------- */

function wpu_bt_content_props( $for_update ) {
	$p = array(
		'title'          => array( 'type' => 'string' ),
		'content'        => array( 'type' => 'string', 'description' => 'Block markup (preferred) or HTML. Filtered like an editor\'s content (no scripts).' ),
		'excerpt'        => array( 'type' => 'string' ),
		'status'         => array( 'type' => 'string', 'enum' => array( 'draft', 'pending', 'private', 'future', 'publish' ), 'description' => 'Default draft. publish only when the person asked.' ),
		'date'           => array( 'type' => 'string', 'description' => 'ISO 8601, for status future.' ),
		'slug'           => array( 'type' => 'string' ),
		'parent'         => array( 'type' => 'integer' ),
		'menu_order'     => array( 'type' => 'integer' ),
		'template'       => array( 'type' => 'string', 'description' => 'Page template file, or "default".' ),
		'terms'          => array( 'type' => 'object', 'description' => 'taxonomy => list of term names or ids, e.g. {"category":["News"]}. Replaces that taxonomy\'s terms.' ),
		'featured_media' => array( 'type' => 'integer', 'description' => 'Attachment id; 0 removes the featured image.' ),
	);
	if ( $for_update ) {
		$p = array( 'id' => array( 'type' => 'integer' ) ) + $p + array(
			'allow_builder_overwrite' => array( 'type' => 'boolean', 'description' => 'Replace content of a page built with Elementor/Divi/Bricks/Beaver. Normally wrong: those builders ignore post content.' ),
		);
	} else {
		$p = array( 'post_type' => array( 'type' => 'string', 'description' => 'Default page.' ) ) + $p;
	}
	return $p;
}

/** Turn tool args into wp_insert_post fields + side effects. Returns array or WP_Error. */
function wpu_bt_post_fields( array $a, $type, $existing_id = 0 ) {
	$f        = array();
	$warnings = array();
	if ( isset( $a['title'] ) ) {
		$f['post_title'] = sanitize_text_field( (string) $a['title'] );
	}
	if ( isset( $a['content'] ) ) {
		list( $f['post_content'], $warnings ) = wpu_bt_clean_content( $a['content'] );
	}
	if ( isset( $a['excerpt'] ) ) {
		$f['post_excerpt'] = sanitize_textarea_field( (string) $a['excerpt'] );
	}
	if ( isset( $a['slug'] ) ) {
		$f['post_name'] = sanitize_title( (string) $a['slug'] );
	}
	if ( isset( $a['parent'] ) ) {
		$parent = absint( $a['parent'] );
		if ( $parent && ( ! get_post( $parent ) || $parent === $existing_id ) ) {
			return wpu_bt_err( 'parent ' . $parent . ' is not a valid post.' );
		}
		$f['post_parent'] = $parent;
	}
	if ( isset( $a['menu_order'] ) ) {
		$f['menu_order'] = (int) $a['menu_order'];
	}
	if ( isset( $a['status'] ) ) {
		$status = (string) $a['status'];
		$pto    = get_post_type_object( $type );
		if ( in_array( $status, array( 'publish', 'future', 'private' ), true ) && ! current_user_can( $pto->cap->publish_posts ) ) {
			return wpu_bt_err( 'You cannot publish ' . $pto->label . '.' );
		}
		$f['post_status'] = $status;
		if ( 'future' === $status ) {
			$ts = isset( $a['date'] ) ? strtotime( (string) $a['date'] ) : false;
			if ( ! $ts || $ts <= time() ) {
				return wpu_bt_err( 'status future needs a date in the future.' );
			}
			$f['post_date_gmt'] = gmdate( 'Y-m-d H:i:s', $ts );
			$f['post_date']     = get_date_from_gmt( $f['post_date_gmt'] );
		}
	}
	if ( isset( $a['template'] ) ) {
		$tpl = (string) $a['template'];
		if ( 'default' !== $tpl && '' !== $tpl && ! array_key_exists( $tpl, wp_get_theme()->get_page_templates( null, $type ) ) ) {
			return wpu_bt_err( 'Unknown template ' . $tpl . '. Known: default, ' . implode( ', ', array_keys( wp_get_theme()->get_page_templates( null, $type ) ) ) );
		}
		$f['page_template'] = $tpl;
	}
	return array( 'fields' => $f, 'warnings' => $warnings );
}

/** Resolve {"taxonomy": [names or ids]} to term ids, creating missing names where allowed. */
function wpu_bt_resolve_terms( $type, $terms ) {
	$out = array();
	foreach ( (array) $terms as $tax => $list ) {
		$tax = sanitize_key( $tax );
		if ( ! in_array( $tax, get_object_taxonomies( $type ), true ) ) {
			return wpu_bt_err( 'Taxonomy ' . $tax . ' does not apply to ' . $type . '.' );
		}
		$taxo = get_taxonomy( $tax );
		$ids  = array();
		foreach ( (array) $list as $t ) {
			if ( is_int( $t ) || ( is_string( $t ) && ctype_digit( $t ) ) ) {
				if ( get_term( (int) $t, $tax ) ) {
					$ids[] = (int) $t;
				}
				continue;
			}
			$name = sanitize_text_field( (string) $t );
			if ( '' === $name ) {
				continue;
			}
			$found = term_exists( $name, $tax );
			if ( ! $found ) {
				if ( ! current_user_can( $taxo->cap->edit_terms ) ) {
					return wpu_bt_err( 'Term "' . $name . '" does not exist in ' . $tax . ' and you cannot create terms.' );
				}
				$found = wp_insert_term( $name, $tax );
				if ( is_wp_error( $found ) ) {
					return $found;
				}
			}
			$ids[] = (int) ( is_array( $found ) ? $found['term_id'] : $found );
		}
		$out[ $tax ] = $ids;
	}
	return $out;
}

/* -------------------------------------------------------------------------
 * Tools
 * ---------------------------------------------------------------------- */

wpu_bt_define_tool( 'content_list', array(
	'title'       => 'List content',
	'description' => 'Pages, posts or any custom post type, newest first, with the builder each one uses.',
	'cap'         => 'edit_posts',
	'props'       => array(
		'post_type' => array( 'type' => 'string', 'description' => 'Default: page and post.' ),
		'status'    => array( 'type' => 'string', 'description' => 'publish, draft, pending, private, future, trash or any (default: all but trash).' ),
		'search'    => array( 'type' => 'string' ),
		'parent'    => array( 'type' => 'integer' ),
		'per_page'  => array( 'type' => 'integer', 'description' => '1-100, default 30' ),
		'page'      => array( 'type' => 'integer' ),
	),
	'run'         => function ( $a ) {
		$types = isset( $a['post_type'] ) ? array( sanitize_key( $a['post_type'] ) ) : array( 'page', 'post' );
		foreach ( $types as $t ) {
			if ( ! wpu_bt_editable_type( $t ) && 'product' !== $t ) {
				return wpu_bt_err( 'Unknown or unsupported post type: ' . $t );
			}
		}
		$status = isset( $a['status'] ) ? sanitize_key( $a['status'] ) : 'any';
		$q      = new WP_Query( array(
			'post_type'      => $types,
			'post_status'    => 'any' === $status ? array( 'publish', 'draft', 'pending', 'private', 'future' ) : $status,
			's'              => isset( $a['search'] ) ? sanitize_text_field( $a['search'] ) : '',
			'post_parent'    => isset( $a['parent'] ) ? absint( $a['parent'] ) : '',
			'posts_per_page' => wpu_bt_int( $a, 'per_page', 30, 1, 100 ),
			'paged'          => wpu_bt_int( $a, 'page', 1, 1, 10000 ),
			'orderby'        => 'modified',
			'order'          => 'DESC',
			'no_found_rows'  => false,
		) );
		$rows = array();
		foreach ( $q->posts as $p ) {
			if ( ! current_user_can( 'edit_post', $p->ID ) ) {
				continue;
			}
			$rows[] = array(
				'id'       => $p->ID,
				'type'     => $p->post_type,
				'title'    => get_the_title( $p ),
				'status'   => $p->post_status,
				'slug'     => $p->post_name,
				'parent'   => $p->post_parent,
				'url'      => get_permalink( $p ),
				'modified' => $p->post_modified_gmt,
				'builder'  => wpu_bt_post_builder( $p->ID ),
			);
		}
		return array( 'total' => (int) $q->found_posts, 'pages' => (int) $q->max_num_pages, 'items' => $rows );
	},
) );

wpu_bt_define_tool( 'content_get', array(
	'title'       => 'Get content',
	'description' => 'One post, page or custom post: fields, terms, featured image, SEO fields, its builder, the raw content and, for Gutenberg, an outline of its blocks with paths for blocks_edit.',
	'cap'         => 'edit_posts',
	'props'       => array(
		'id'              => array( 'type' => 'integer' ),
		'include_content' => array( 'type' => 'boolean', 'description' => 'Default true (false for builder pages).' ),
		'include_meta'    => array( 'type' => 'boolean', 'description' => 'Custom fields that are not hidden (no leading underscore).' ),
	),
	'required'    => array( 'id' ),
	'run'         => function ( $a ) {
		$id = absint( $a['id'] );
		$p  = get_post( $id );
		if ( ! $p || ! current_user_can( 'edit_post', $id ) ) {
			return wpu_bt_err( 'No post ' . $id . ' that you can edit.' );
		}
		$builder = wpu_bt_post_builder( $id );
		$terms   = array();
		foreach ( get_object_taxonomies( $p->post_type ) as $tax ) {
			$list = wp_get_object_terms( $id, $tax, array( 'fields' => 'id=>name' ) );
			if ( ! is_wp_error( $list ) && $list ) {
				$terms[ $tax ] = $list;
			}
		}
		$thumb = get_post_thumbnail_id( $id );
		$out   = array(
			'id'             => $id,
			'type'           => $p->post_type,
			'status'         => $p->post_status,
			'title'          => $p->post_title,
			'slug'           => $p->post_name,
			'url'            => get_permalink( $p ),
			'edit_url'       => get_edit_post_link( $id, 'raw' ),
			'parent'         => $p->post_parent,
			'menu_order'     => $p->menu_order,
			'template'       => get_page_template_slug( $id ) ? get_page_template_slug( $id ) : 'default',
			'author'         => get_the_author_meta( 'user_login', $p->post_author ),
			'date'           => $p->post_date_gmt,
			'modified'       => $p->post_modified_gmt,
			'excerpt'        => $p->post_excerpt,
			'builder'        => $builder,
			'terms'          => $terms ? $terms : new stdClass(),
			'featured_media' => $thumb ? array( 'id' => $thumb, 'url' => wp_get_attachment_url( $thumb ) ) : null,
			'seo'            => wpu_bt_seo_read( $id, wpu_bt_seo_plugin() ),
		);
		$builder_page = in_array( $builder, array( 'elementor', 'divi', 'bricks', 'beaver_builder', 'breakdance', 'seedprod' ), true );
		if ( wpu_bt_bool( $a, 'include_content', ! $builder_page ) ) {
			$out['content'] = wpu_bt_trim( $p->post_content, 100000 );
		}
		if ( 'gutenberg' === $builder ) {
			$out['blocks'] = wpu_bt_block_outline( parse_blocks( $p->post_content ) );
		}
		if ( in_array( $builder, array( 'divi', 'bricks', 'beaver_builder', 'breakdance', 'seedprod' ), true ) ) {
			$out['note'] = ucfirst( str_replace( '_', ' ', $builder ) ) . ' page: read its text with builder_page_text and change it with builder_replace_text.';
		}
		if ( 'gutenberg' === $builder ) {
			$out['block_plugins'] = wpu_bt_block_namespaces( $p->post_content );
		}
		if ( 'elementor' === $builder ) {
			$out['note'] = 'Elementor page: read its text with builder_page_text and change it with builder_replace_text.';
		}
		if ( wpu_bt_bool( $a, 'include_meta' ) ) {
			$meta = array();
			foreach ( get_post_meta( $id ) as $k => $vals ) {
				if ( '_' === $k[0] || is_protected_meta( $k, 'post' ) ) {
					continue;
				}
				$v          = maybe_unserialize( $vals[0] );
				$meta[ $k ] = is_scalar( $v ) ? wpu_bt_trim( $v, 2000 ) : '(structured value)';
			}
			$out['meta'] = $meta ? $meta : new stdClass();
		}
		return $out;
	},
) );

wpu_bt_define_tool( 'content_create', array(
	'title'       => 'Create content',
	'description' => 'Create a page, post or custom post. Status is draft unless you set it. Write Gutenberg block markup for the content. Returns the id, a preview link and a change_id (undo moves it to the trash).',
	'cap'         => 'edit_posts',
	'props'       => wpu_bt_content_props( false ),
	'required'    => array( 'title' ),
	'write'       => true,
	'run'         => function ( $a ) {
		$type = isset( $a['post_type'] ) ? sanitize_key( $a['post_type'] ) : 'page';
		if ( ! wpu_bt_editable_type( $type ) ) {
			return wpu_bt_err( 'Unsupported post type: ' . $type . ( 'product' === $type ? '. Use woo_product_create.' : '' ) );
		}
		$pto = get_post_type_object( $type );
		if ( ! current_user_can( $pto->cap->create_posts ) ) {
			return wpu_bt_err( 'You cannot create ' . $pto->label . '.' );
		}
		$built = wpu_bt_post_fields( $a + array( 'status' => 'draft' ), $type );
		if ( is_wp_error( $built ) ) {
			return $built;
		}
		$terms = isset( $a['terms'] ) ? wpu_bt_resolve_terms( $type, $a['terms'] ) : array();
		if ( is_wp_error( $terms ) ) {
			return $terms;
		}
		$f              = $built['fields'];
		$f['post_type'] = $type;
		$id             = wp_insert_post( wp_slash( $f ), true );
		if ( is_wp_error( $id ) ) {
			return $id;
		}
		foreach ( $terms as $tax => $ids ) {
			wp_set_object_terms( $id, $ids, $tax );
		}
		if ( ! empty( $a['featured_media'] ) && 'attachment' === get_post_type( (int) $a['featured_media'] ) ) {
			set_post_thumbnail( $id, (int) $a['featured_media'] );
		}
		$cid = wpu_bt_change_add( 'content_create', 'Created ' . $type . ' #' . $id . ' "' . $f['post_title'] . '"', array( 'kind' => 'trash', 'id' => $id ) );
		return array(
			'id'        => $id,
			'status'    => get_post_status( $id ),
			'url'       => get_permalink( $id ),
			'preview'   => get_preview_post_link( $id ),
			'edit_url'  => get_edit_post_link( $id, 'raw' ),
			'warnings'  => $built['warnings'],
			'change_id' => $cid,
		);
	},
) );

wpu_bt_define_tool( 'content_update', array(
	'title'       => 'Update content',
	'description' => 'Change fields of a post, page or custom post: title, content, excerpt, status, slug, parent, order, template, terms, featured image. Only the fields you send change. Refuses to overwrite the content of a page built with Elementor or another builder. Returns a change_id for undo.',
	'cap'         => 'edit_posts',
	'props'       => wpu_bt_content_props( true ),
	'required'    => array( 'id' ),
	'write'       => true,
	'run'         => function ( $a ) {
		$id = absint( $a['id'] );
		$p  = get_post( $id );
		if ( ! $p || ! current_user_can( 'edit_post', $id ) ) {
			return wpu_bt_err( 'No post ' . $id . ' that you can edit.' );
		}
		if ( ! wpu_bt_editable_type( $p->post_type ) ) {
			return wpu_bt_err( 'Unsupported post type: ' . $p->post_type . ( 'product' === $p->post_type ? '. Use woo_product_update.' : '' ) );
		}
		$builder = wpu_bt_post_builder( $id );
		if ( isset( $a['content'] ) && in_array( $builder, array( 'elementor', 'divi', 'bricks', 'beaver_builder', 'breakdance', 'seedprod' ), true ) && ! wpu_bt_bool( $a, 'allow_builder_overwrite' ) ) {
			return wpu_bt_err( 'This page is built with ' . $builder . ', which ignores post content. ' . 'Use builder_replace_text to change its text.' );
		}
		$built = wpu_bt_post_fields( $a, $p->post_type, $id );
		if ( is_wp_error( $built ) ) {
			return $built;
		}
		$terms = isset( $a['terms'] ) ? wpu_bt_resolve_terms( $p->post_type, $a['terms'] ) : array();
		if ( is_wp_error( $terms ) ) {
			return $terms;
		}
		$f      = $built['fields'];
		$before = array();
		foreach ( array_keys( $f ) as $k ) {
			if ( 'page_template' === $k || 'post_date' === $k || 'post_date_gmt' === $k ) {
				continue;
			}
			$before[ $k ] = $p->$k;
		}
		$undo_items = array();
		$post_undo  = array( 'kind' => 'post', 'id' => $id, 'fields' => $before );
		if ( $terms ) {
			$post_undo['terms'] = array();
			foreach ( array_keys( $terms ) as $tax ) {
				$post_undo['terms'][ $tax ] = wp_get_object_terms( $id, $tax, array( 'fields' => 'ids' ) );
			}
		}
		if ( array_key_exists( 'featured_media', $a ) ) {
			$post_undo['thumbnail'] = (int) get_post_thumbnail_id( $id );
		}
		$undo_items[] = $post_undo;
		if ( isset( $f['page_template'] ) ) {
			$old          = get_post_meta( $id, '_wp_page_template', true );
			$undo_items[] = array( 'kind' => 'meta', 'id' => $id, 'values' => array( '_wp_page_template' => '' === $old ? null : $old ) );
		}

		if ( $f ) {
			$f['ID'] = $id;
			$r       = wp_update_post( wp_slash( $f ), true );
			if ( is_wp_error( $r ) ) {
				return $r;
			}
		}
		foreach ( $terms as $tax => $ids ) {
			wp_set_object_terms( $id, $ids, $tax );
		}
		if ( array_key_exists( 'featured_media', $a ) ) {
			$att = (int) $a['featured_media'];
			if ( 0 === $att ) {
				delete_post_thumbnail( $id );
			} elseif ( 'attachment' === get_post_type( $att ) ) {
				set_post_thumbnail( $id, $att );
			}
		}
		wpu_bt_after_content_write( $id );
		$changed = array_merge( array_keys( $before ), array_keys( $terms ), array_key_exists( 'featured_media', $a ) ? array( 'featured_media' ) : array(), isset( $f['page_template'] ) ? array( 'template' ) : array() );
		$cid     = wpu_bt_change_add( 'content_update', 'Updated #' . $id . ' "' . get_the_title( $id ) . '": ' . implode( ', ', $changed ), array( 'kind' => 'multi', 'items' => $undo_items ) );
		return array(
			'id'        => $id,
			'changed'   => $changed,
			'status'    => get_post_status( $id ),
			'url'       => get_permalink( $id ),
			'preview'   => get_preview_post_link( $id ),
			'warnings'  => $built['warnings'],
			'change_id' => $cid,
		);
	},
) );

wpu_bt_define_tool( 'blocks_edit', array(
	'title'       => 'Edit Gutenberg blocks',
	'description' => 'Targeted edits to a Gutenberg page without resending it. Operations run in order: '
		. '{"op":"replace_text","find":"...","replace":"...","limit":N} changes visible text, never block attributes; '
		. '{"op":"replace","path":"2.1","markup":"<!-- wp:... -->"} swaps a block for new markup; '
		. '{"op":"remove","path":"3"}; '
		. '{"op":"insert","markup":"...","before":"2" | "after":"2.0" | "position":"start"|"end"}. '
		. 'Paths come from content_get (blocks outline). Paths are read before any operation runs, so list removals last or re-read between calls.',
	'cap'         => 'edit_posts',
	'props'       => array(
		'id'         => array( 'type' => 'integer' ),
		'operations' => array( 'type' => 'array', 'items' => array( 'type' => 'object' ), 'description' => 'Up to 50 operations.' ),
		'dry_run'    => array( 'type' => 'boolean', 'description' => 'Show the result without saving.' ),
	),
	'required'    => array( 'id', 'operations' ),
	'write'       => true,
	'run'         => function ( $a ) {
		$id = absint( $a['id'] );
		$p  = get_post( $id );
		if ( ! $p || ! current_user_can( 'edit_post', $id ) ) {
			return wpu_bt_err( 'No post ' . $id . ' that you can edit.' );
		}
		$builder = wpu_bt_post_builder( $id );
		if ( ! in_array( $builder, array( 'gutenberg', 'classic', 'empty' ), true ) ) {
			return wpu_bt_err( 'This page is built with ' . $builder . ', not Gutenberg.' );
		}
		$ops = (array) $a['operations'];
		if ( count( $ops ) > 50 ) {
			return wpu_bt_err( 'At most 50 operations per call.' );
		}
		$content = (string) $p->post_content;
		$log     = array();
		foreach ( $ops as $n => $op ) {
			$op   = (array) $op;
			$kind = isset( $op['op'] ) ? (string) $op['op'] : '';
			if ( 'replace_text' === $kind ) {
				$find = isset( $op['find'] ) ? (string) $op['find'] : '';
				if ( '' === $find ) {
					return wpu_bt_err( 'Operation ' . $n . ': find is empty.' );
				}
				$limit = isset( $op['limit'] ) ? max( 1, min( 500, (int) $op['limit'] ) ) : 500;
				list( $content, $count ) = wpu_bt_replace_outside_comments( $content, $find, isset( $op['replace'] ) ? (string) $op['replace'] : '', $limit );
				$log[] = array( 'op' => $n, 'replaced' => $count );
				continue;
			}
			$blocks = parse_blocks( $content );
			$new    = isset( $op['markup'] ) ? wpu_bt_markup_blocks( wp_kses_post( (string) $op['markup'] ) ) : array();
			if ( in_array( $kind, array( 'replace', 'insert' ), true ) && ! $new ) {
				return wpu_bt_err( 'Operation ' . $n . ': markup has no blocks.' );
			}
			if ( 'insert' === $kind && isset( $op['position'] ) ) {
				$ws = array();
				foreach ( $new as $i => $b ) {
					if ( $i > 0 ) {
						$ws[] = wpu_bt_ws_block();
					}
					$ws[] = $b;
				}
				if ( 'start' === $op['position'] ) {
					$blocks = array_merge( $ws, array( wpu_bt_ws_block() ), $blocks );
				} else {
					$blocks = array_merge( $blocks, array( wpu_bt_ws_block() ), $ws );
				}
				$content = serialize_blocks( $blocks );
				$log[]   = array( 'op' => $n, 'inserted' => count( $new ), 'at' => $op['position'] );
				continue;
			}
			$mode = $kind;
			$path = null;
			if ( 'insert' === $kind ) {
				$mode = isset( $op['before'] ) ? 'before' : 'after';
				$path = wpu_bt_parse_path( isset( $op['before'] ) ? $op['before'] : ( isset( $op['after'] ) ? $op['after'] : '' ) );
			} elseif ( in_array( $kind, array( 'replace', 'remove' ), true ) ) {
				$path = wpu_bt_parse_path( isset( $op['path'] ) ? $op['path'] : '' );
			} else {
				return wpu_bt_err( 'Operation ' . $n . ': unknown op "' . $kind . '". Use replace_text, replace, remove or insert.' );
			}
			if ( null === $path ) {
				return wpu_bt_err( 'Operation ' . $n . ': give a path like "2" or "2.0.1" (insert also takes position start/end).' );
			}
			$r = wpu_bt_tree_op( $blocks, $path, $mode, $new );
			if ( is_wp_error( $r ) ) {
				return wpu_bt_err( 'Operation ' . $n . ': ' . $r->get_error_message() );
			}
			$content = serialize_blocks( $blocks );
			$log[]   = array( 'op' => $n, $mode => implode( '.', $path ) );
		}
		list( $content, $warnings ) = wpu_bt_clean_content( $content );
		if ( wpu_bt_bool( $a, 'dry_run' ) ) {
			return array( 'dry_run' => true, 'operations' => $log, 'warnings' => $warnings, 'blocks' => wpu_bt_block_outline( parse_blocks( $content ) ) );
		}
		if ( $content === $p->post_content ) {
			return array( 'id' => $id, 'operations' => $log, 'changed' => false, 'note' => 'Nothing changed.' );
		}
		$r = wp_update_post( wp_slash( array( 'ID' => $id, 'post_content' => $content ) ), true );
		if ( is_wp_error( $r ) ) {
			return $r;
		}
		wpu_bt_after_content_write( $id );
		$cid = wpu_bt_change_add( 'blocks_edit', 'Edited blocks on #' . $id . ' "' . get_the_title( $id ) . '" (' . count( $log ) . ' operations)', array( 'kind' => 'post', 'id' => $id, 'fields' => array( 'post_content' => $p->post_content ) ) );
		return array( 'id' => $id, 'operations' => $log, 'warnings' => $warnings, 'preview' => get_preview_post_link( $id ), 'change_id' => $cid );
	},
) );

wpu_bt_define_tool( 'block_types_list', array(
	'title'       => 'Block types',
	'description' => 'Blocks registered on this site (core, theme and plugin blocks) with their attributes, so the markup you write is valid here.',
	'cap'         => 'edit_posts',
	'props'       => array(
		'search'    => array( 'type' => 'string', 'description' => 'Part of a name or title.' ),
		'namespace' => array( 'type' => 'string', 'description' => 'e.g. core, kadence, woocommerce' ),
		'names'     => array( 'type' => 'array', 'items' => array( 'type' => 'string' ), 'description' => 'Exact block names to get in full.' ),
		'attributes' => array( 'type' => 'boolean', 'description' => 'Include attributes (always on when names are given).' ),
	),
	'run'         => function ( $a ) {
		$names  = isset( $a['names'] ) ? array_map( 'strval', (array) $a['names'] ) : array();
		$search = strtolower( wpu_bt_str( $a, 'search' ) );
		$ns     = sanitize_key( wpu_bt_str( $a, 'namespace' ) );
		$attrs  = $names || wpu_bt_bool( $a, 'attributes' );
		$out    = array();
		foreach ( WP_Block_Type_Registry::get_instance()->get_all_registered() as $name => $bt ) {
			if ( $names && ! in_array( $name, $names, true ) ) {
				continue;
			}
			if ( $ns && 0 !== strpos( $name, $ns . '/' ) ) {
				continue;
			}
			if ( $search && false === strpos( strtolower( $name . ' ' . $bt->title ), $search ) ) {
				continue;
			}
			$row = array(
				'name'     => $name,
				'title'    => $bt->title,
				'category' => $bt->category,
				'dynamic'  => $bt->is_dynamic(),
				'parent'   => $bt->parent,
			);
			if ( $attrs ) {
				$at = array();
				foreach ( (array) $bt->attributes as $k => $def ) {
					if ( in_array( $k, array( 'lock', 'metadata' ), true ) ) {
						continue;
					}
					$at[ $k ] = array_intersect_key( (array) $def, array_flip( array( 'type', 'default', 'enum', 'source', 'selector' ) ) );
				}
				$row['attributes']  = $at ? $at : new stdClass();
				$row['supports']    = array_keys( (array) $bt->supports );
				$row['description'] = $bt->description;
			}
			$out[] = $row;
			if ( count( $out ) >= 400 ) {
				break;
			}
		}
		return array( 'count' => count( $out ), 'blocks' => $out );
	},
) );

wpu_bt_define_tool( 'block_patterns_list', array(
	'title'       => 'Block patterns',
	'description' => 'Ready-made block layouts the theme and plugins provide. Ask for up to 5 by name to get their markup, then adapt it.',
	'cap'         => 'edit_posts',
	'props'       => array(
		'search' => array( 'type' => 'string' ),
		'names'  => array( 'type' => 'array', 'items' => array( 'type' => 'string' ), 'description' => 'Up to 5 pattern names to return with markup.' ),
	),
	'run'         => function ( $a ) {
		$names  = isset( $a['names'] ) ? array_slice( array_map( 'strval', (array) $a['names'] ), 0, 5 ) : array();
		$search = strtolower( wpu_bt_str( $a, 'search' ) );
		$out    = array();
		foreach ( WP_Block_Patterns_Registry::get_instance()->get_all_registered() as $pat ) {
			if ( $names && ! in_array( $pat['name'], $names, true ) ) {
				continue;
			}
			if ( $search && false === strpos( strtolower( $pat['name'] . ' ' . $pat['title'] . ' ' . ( isset( $pat['description'] ) ? $pat['description'] : '' ) ), $search ) ) {
				continue;
			}
			$row = array(
				'name'       => $pat['name'],
				'title'      => $pat['title'],
				'categories' => isset( $pat['categories'] ) ? $pat['categories'] : array(),
			);
			if ( $names ) {
				$row['content'] = isset( $pat['content'] ) ? $pat['content'] : '';
			}
			$out[] = $row;
			if ( count( $out ) >= 200 ) {
				break;
			}
		}
		return array( 'count' => count( $out ), 'patterns' => $out );
	},
) );

/** Global colour palettes kept by popular themes and block plugins (Kadence, Astra, GeneratePress). */
function wpu_bt_theme_palettes() {
	$out = array();
	$k   = get_option( 'kadence_global_palette' );
	$k   = is_string( $k ) ? json_decode( $k, true ) : $k;
	if ( is_array( $k ) && ! empty( $k['palette'] ) ) {
		$out['kadence'] = array(
			'use'    => 'Kadence blocks: colour values like "palette1"; CSS var(--global-palette1)',
			'colors' => array_map( function ( $c ) {
				return array_intersect_key( (array) $c, array_flip( array( 'slug', 'name', 'color' ) ) );
			}, (array) $k['palette'] ),
		);
	}
	$astra = get_option( 'astra-settings' );
	if ( is_array( $astra ) && ! empty( $astra['global-color-palette']['palette'] ) ) {
		$cols = array();
		foreach ( array_values( (array) $astra['global-color-palette']['palette'] ) as $i => $c ) {
			$cols[] = array( 'slug' => 'ast-global-color-' . $i, 'color' => $c );
		}
		$out['astra'] = array( 'use' => 'CSS var(--ast-global-color-N)', 'colors' => $cols );
	}
	$gp = get_option( 'generate_settings' );
	if ( is_array( $gp ) && ! empty( $gp['global_colors'] ) ) {
		$out['generatepress'] = array( 'use' => 'CSS var(--slug)', 'colors' => array_values( (array) $gp['global_colors'] ) );
	}
	return $out ? $out : new stdClass();
}

wpu_bt_define_tool( 'theme_design_tokens', array(
	'title'       => 'Theme design tokens',
	'description' => 'The site\'s colours, gradients, font sizes, font families, spacing sizes and content widths from theme.json (or the classic theme\'s editor settings), plus Kadence, Astra and GeneratePress global palettes. Use their slugs in block attributes, e.g. {"backgroundColor":"primary"}.',
	'cap'         => 'edit_posts',
	'run'         => function () {
		$s    = function_exists( 'wp_get_global_settings' ) ? wp_get_global_settings() : array();
		$pick = function ( $node ) {
			$out = array();
			foreach ( array( 'theme', 'custom', 'default' ) as $origin ) {
				if ( ! empty( $node[ $origin ] ) ) {
					foreach ( (array) $node[ $origin ] as $item ) {
						$item['origin'] = $origin;
						$out[]          = $item;
					}
				}
			}
			return $out;
		};
		$out = array(
			'palette'       => isset( $s['color']['palette'] ) ? $pick( $s['color']['palette'] ) : array(),
			'gradients'     => isset( $s['color']['gradients'] ) ? array_slice( $pick( $s['color']['gradients'] ), 0, 30 ) : array(),
			'font_sizes'    => isset( $s['typography']['fontSizes'] ) ? $pick( $s['typography']['fontSizes'] ) : array(),
			'font_families' => isset( $s['typography']['fontFamilies'] ) ? array_map( function ( $f ) {
				return array_intersect_key( $f, array_flip( array( 'slug', 'name', 'fontFamily', 'origin' ) ) );
			}, $pick( $s['typography']['fontFamilies'] ) ) : array(),
			'spacing_sizes' => isset( $s['spacing']['spacingSizes'] ) ? $pick( $s['spacing']['spacingSizes'] ) : array(),
			'layout'        => isset( $s['layout'] ) ? $s['layout'] : new stdClass(),
		);
		if ( ! $out['palette'] && get_theme_support( 'editor-color-palette' ) ) {
			$out['palette'] = (array) current( (array) get_theme_support( 'editor-color-palette' ) );
		}
		if ( ! $out['font_sizes'] && get_theme_support( 'editor-font-sizes' ) ) {
			$out['font_sizes'] = (array) current( (array) get_theme_support( 'editor-font-sizes' ) );
		}
		$out['block_theme']    = function_exists( 'wp_is_block_theme' ) && wp_is_block_theme();
		$out['theme_palettes'] = wpu_bt_theme_palettes();
		return $out;
	},
) );

wpu_bt_define_tool( 'content_search_replace', array(
	'title'       => 'Search and replace in content',
	'description' => 'Find text across pages and posts and optionally replace it. dry_run (the default) lists matches and changes nothing. Changes visible text only, never block attributes; skips pages built with Elementor or other builders (use builder_replace_text for those). One change_id undoes the whole run.',
	'cap'         => 'edit_others_posts',
	'props'       => array(
		'find'           => array( 'type' => 'string' ),
		'replace'        => array( 'type' => 'string' ),
		'post_types'     => array( 'type' => 'array', 'items' => array( 'type' => 'string' ), 'description' => 'Default page and post.' ),
		'case_sensitive' => array( 'type' => 'boolean', 'description' => 'Default true.' ),
		'dry_run'        => array( 'type' => 'boolean', 'description' => 'Default true.' ),
		'max_posts'      => array( 'type' => 'integer', 'description' => '1-200, default 100.' ),
	),
	'required'    => array( 'find' ),
	'write'       => true,
	'run'         => function ( $a ) {
		$find = (string) $a['find'];
		if ( strlen( $find ) < 2 ) {
			return wpu_bt_err( 'find must be at least 2 characters.' );
		}
		$dry   = wpu_bt_bool( $a, 'dry_run', true );
		$case  = wpu_bt_bool( $a, 'case_sensitive', true );
		$types = isset( $a['post_types'] ) ? array_map( 'sanitize_key', (array) $a['post_types'] ) : array( 'page', 'post' );
		foreach ( $types as $t ) {
			if ( ! wpu_bt_editable_type( $t ) ) {
				return wpu_bt_err( 'Unsupported post type: ' . $t );
			}
		}
		if ( ! $dry && ! array_key_exists( 'replace', $a ) ) {
			return wpu_bt_err( 'replace is required when dry_run is false.' );
		}
		$q = new WP_Query( array(
			'post_type'      => $types,
			'post_status'    => array( 'publish', 'draft', 'pending', 'private', 'future' ),
			's'              => $find,
			'search_columns' => array( 'post_content', 'post_title', 'post_excerpt' ),
			'posts_per_page' => wpu_bt_int( $a, 'max_posts', 100, 1, 200 ),
			'no_found_rows'  => true,
		) );
		$matches = array();
		$skipped = array();
		$undo    = array();
		foreach ( $q->posts as $p ) {
			if ( ! current_user_can( 'edit_post', $p->ID ) ) {
				continue;
			}
			$builder = wpu_bt_post_builder( $p->ID );
			if ( ! in_array( $builder, array( 'gutenberg', 'classic', 'empty' ), true ) ) {
				$skipped[] = array( 'id' => $p->ID, 'title' => $p->post_title, 'builder' => $builder );
				continue;
			}
			list( $new_content, $n ) = wpu_bt_replace_outside_comments( $p->post_content, $find, isset( $a['replace'] ) ? (string) $a['replace'] : $find, 1000, $case );
			$title_n                 = $case ? substr_count( $p->post_title, $find ) : substr_count( strtolower( $p->post_title ), strtolower( $find ) );
			if ( ! $n && ! $title_n ) {
				continue;
			}
			$matches[] = array( 'id' => $p->ID, 'title' => $p->post_title, 'url' => get_permalink( $p ), 'in_content' => $n, 'in_title' => $title_n );
			if ( $dry ) {
				continue;
			}
			$fields = array( 'ID' => $p->ID, 'post_content' => wp_kses_post( $new_content ) );
			if ( $title_n ) {
				$fields['post_title'] = sanitize_text_field( $case ? str_replace( $find, (string) $a['replace'], $p->post_title ) : str_ireplace( $find, (string) $a['replace'], $p->post_title ) );
			}
			$r = wp_update_post( wp_slash( $fields ), true );
			if ( ! is_wp_error( $r ) ) {
				$undo[] = array( 'kind' => 'post', 'id' => $p->ID, 'fields' => array( 'post_content' => $p->post_content, 'post_title' => $p->post_title ) );
			}
		}
		$out = array( 'dry_run' => $dry, 'matches' => $matches, 'skipped_builder_pages' => $skipped );
		if ( ! $dry && $undo ) {
			$out['change_id'] = wpu_bt_change_add( 'content_search_replace', 'Replaced "' . substr( $find, 0, 40 ) . '" in ' . count( $undo ) . ' posts', array( 'kind' => 'multi', 'items' => $undo ) );
		}
		return $out;
	},
) );

wpu_bt_define_tool( 'terms_list', array(
	'title'       => 'List terms',
	'description' => 'Categories, tags or any taxonomy\'s terms with counts.',
	'cap'         => 'edit_posts',
	'props'       => array(
		'taxonomy' => array( 'type' => 'string', 'description' => 'e.g. category, post_tag, product_cat' ),
		'search'   => array( 'type' => 'string' ),
	),
	'required'    => array( 'taxonomy' ),
	'run'         => function ( $a ) {
		$tax = sanitize_key( $a['taxonomy'] );
		if ( ! taxonomy_exists( $tax ) ) {
			return wpu_bt_err( 'Unknown taxonomy ' . $tax );
		}
		$terms = get_terms( array( 'taxonomy' => $tax, 'hide_empty' => false, 'number' => 300, 'search' => wpu_bt_str( $a, 'search' ) ) );
		if ( is_wp_error( $terms ) ) {
			return $terms;
		}
		$out = array();
		foreach ( $terms as $t ) {
			$out[] = array( 'id' => $t->term_id, 'name' => $t->name, 'slug' => $t->slug, 'parent' => $t->parent, 'count' => $t->count );
		}
		return array( 'taxonomy' => $tax, 'terms' => $out );
	},
) );

/* -------------------------------------------------------------------------
 * Media
 * ---------------------------------------------------------------------- */

function wpu_bt_media_types() {
	return array(
		'jpg|jpeg|jpe' => 'image/jpeg',
		'png'          => 'image/png',
		'gif'          => 'image/gif',
		'webp'         => 'image/webp',
		'avif'         => 'image/avif',
		'pdf'          => 'application/pdf',
	);
}

wpu_bt_define_tool( 'media_upload', array(
	'title'       => 'Upload media',
	'description' => 'Add an image (jpg, png, gif, webp, avif) or PDF to the Media Library from a public https address or from base64 data, with alt text. Max 25 MB. SVG is refused.',
	'cap'         => 'upload_files',
	'props'       => array(
		'url'         => array( 'type' => 'string', 'description' => 'Public https address of the file.' ),
		'content_b64' => array( 'type' => 'string', 'description' => 'File contents in base64 (instead of url).' ),
		'filename'    => array( 'type' => 'string', 'description' => 'Needed with content_b64, e.g. hero.webp' ),
		'alt'         => array( 'type' => 'string' ),
		'title'       => array( 'type' => 'string' ),
		'attach_to'   => array( 'type' => 'integer', 'description' => 'Post id to attach it to.' ),
	),
	'write'       => true,
	'run'         => function ( $a ) {
		require_once ABSPATH . 'wp-admin/includes/file.php';
		require_once ABSPATH . 'wp-admin/includes/media.php';
		require_once ABSPATH . 'wp-admin/includes/image.php';
		$max = 25 * MB_IN_BYTES;
		if ( ! empty( $a['url'] ) ) {
			$url = esc_url_raw( (string) $a['url'], array( 'https', 'http' ) );
			if ( '' === $url ) {
				return wpu_bt_err( 'Not a valid address.' );
			}
			$name = sanitize_file_name( ! empty( $a['filename'] ) ? (string) $a['filename'] : basename( (string) wp_parse_url( $url, PHP_URL_PATH ) ) );
			// download_url() uses wp_safe_remote_get(): private and local addresses are refused.
			$tmp = download_url( $url, 60 );
			if ( is_wp_error( $tmp ) ) {
				return wpu_bt_err( 'Could not download: ' . $tmp->get_error_message() );
			}
		} elseif ( ! empty( $a['content_b64'] ) ) {
			$name  = sanitize_file_name( wpu_bt_str( $a, 'filename' ) );
			$bytes = base64_decode( (string) $a['content_b64'], true );
			if ( '' === $name || false === $bytes ) {
				return wpu_bt_err( 'content_b64 must be base64 and filename is required.' );
			}
			if ( strlen( $bytes ) > $max ) {
				return wpu_bt_err( 'File is larger than 25 MB.' );
			}
			$tmp = wp_tempnam( $name );
			file_put_contents( $tmp, $bytes ); // phpcs:ignore WordPress.WP.AlternativeFunctions
		} else {
			return wpu_bt_err( 'Send url or content_b64.' );
		}
		if ( filesize( $tmp ) > $max ) {
			wp_delete_file( $tmp );
			return wpu_bt_err( 'File is larger than 25 MB.' );
		}
		$check = wp_check_filetype_and_ext( $tmp, $name, wpu_bt_media_types() );
		if ( empty( $check['type'] ) ) {
			wp_delete_file( $tmp );
			return wpu_bt_err( 'Only jpg, png, gif, webp, avif and pdf files are accepted, and the contents must match the extension.' );
		}
		if ( ! empty( $check['proper_filename'] ) ) {
			$name = $check['proper_filename'];
		}
		$parent = isset( $a['attach_to'] ) ? absint( $a['attach_to'] ) : 0;
		if ( $parent && ! current_user_can( 'edit_post', $parent ) ) {
			$parent = 0;
		}
		$id = media_handle_sideload(
			array( 'name' => $name, 'tmp_name' => $tmp ),
			$parent,
			isset( $a['title'] ) ? sanitize_text_field( (string) $a['title'] ) : null,
			array()
		);
		if ( is_wp_error( $id ) ) {
			wp_delete_file( $tmp );
			return $id;
		}
		if ( isset( $a['alt'] ) ) {
			update_post_meta( $id, '_wp_attachment_image_alt', sanitize_text_field( (string) $a['alt'] ) );
		}
		$cid = wpu_bt_change_add( 'media_upload', 'Uploaded ' . $name . ' (#' . $id . ')', array( 'kind' => 'trash', 'id' => $id ) );
		return array( 'id' => $id, 'url' => wp_get_attachment_url( $id ), 'mime' => get_post_mime_type( $id ), 'change_id' => $cid );
	},
) );

wpu_bt_define_tool( 'media_list', array(
	'title'       => 'List media',
	'description' => 'Media Library items, newest first, with address, size and alt text.',
	'cap'         => 'upload_files',
	'props'       => array(
		'search'   => array( 'type' => 'string' ),
		'type'     => array( 'type' => 'string', 'enum' => array( 'image', 'application', 'video', 'audio' ) ),
		'missing_alt' => array( 'type' => 'boolean', 'description' => 'Only images without alt text.' ),
		'per_page' => array( 'type' => 'integer', 'description' => '1-100, default 40' ),
		'page'     => array( 'type' => 'integer' ),
	),
	'run'         => function ( $a ) {
		$args = array(
			'post_type'      => 'attachment',
			'post_status'    => 'inherit',
			's'              => wpu_bt_str( $a, 'search' ),
			'posts_per_page' => wpu_bt_int( $a, 'per_page', 40, 1, 100 ),
			'paged'          => wpu_bt_int( $a, 'page', 1, 1, 10000 ),
		);
		if ( ! empty( $a['type'] ) ) {
			$args['post_mime_type'] = (string) $a['type'];
		}
		if ( wpu_bt_bool( $a, 'missing_alt' ) ) {
			$args['post_mime_type'] = 'image';
			$args['meta_query']     = array( // phpcs:ignore WordPress.DB.SlowDBQuery
				'relation' => 'OR',
				array( 'key' => '_wp_attachment_image_alt', 'compare' => 'NOT EXISTS' ),
				array( 'key' => '_wp_attachment_image_alt', 'value' => '' ),
			);
		}
		$q   = new WP_Query( $args );
		$out = array();
		foreach ( $q->posts as $p ) {
			$meta  = wp_get_attachment_metadata( $p->ID );
			$out[] = array(
				'id'     => $p->ID,
				'title'  => $p->post_title,
				'url'    => wp_get_attachment_url( $p->ID ),
				'mime'   => $p->post_mime_type,
				'width'  => isset( $meta['width'] ) ? (int) $meta['width'] : null,
				'height' => isset( $meta['height'] ) ? (int) $meta['height'] : null,
				'alt'    => (string) get_post_meta( $p->ID, '_wp_attachment_image_alt', true ),
				'date'   => $p->post_date_gmt,
			);
		}
		return array( 'total' => (int) $q->found_posts, 'items' => $out );
	},
) );

wpu_bt_define_tool( 'media_update', array(
	'title'       => 'Update media details',
	'description' => 'Change an image\'s alt text, title or caption. Returns a change_id for undo.',
	'cap'         => 'upload_files',
	'props'       => array(
		'id'      => array( 'type' => 'integer' ),
		'alt'     => array( 'type' => 'string' ),
		'title'   => array( 'type' => 'string' ),
		'caption' => array( 'type' => 'string' ),
	),
	'required'    => array( 'id' ),
	'write'       => true,
	'run'         => function ( $a ) {
		$id = absint( $a['id'] );
		$p  = get_post( $id );
		if ( ! $p || 'attachment' !== $p->post_type || ! current_user_can( 'edit_post', $id ) ) {
			return wpu_bt_err( 'No media item ' . $id . ' that you can edit.' );
		}
		$items = array();
		if ( isset( $a['alt'] ) ) {
			$old     = get_post_meta( $id, '_wp_attachment_image_alt', true );
			$items[] = array( 'kind' => 'meta', 'id' => $id, 'values' => array( '_wp_attachment_image_alt' => '' === $old ? null : $old ) );
			update_post_meta( $id, '_wp_attachment_image_alt', sanitize_text_field( (string) $a['alt'] ) );
		}
		$f = array();
		if ( isset( $a['title'] ) ) {
			$f['post_title'] = sanitize_text_field( (string) $a['title'] );
		}
		if ( isset( $a['caption'] ) ) {
			$f['post_excerpt'] = sanitize_textarea_field( (string) $a['caption'] );
		}
		if ( $f ) {
			$items[] = array( 'kind' => 'post', 'id' => $id, 'fields' => array( 'post_title' => $p->post_title, 'post_excerpt' => $p->post_excerpt ) );
			$f['ID'] = $id;
			wp_update_post( wp_slash( $f ) );
		}
		if ( ! $items ) {
			return wpu_bt_err( 'Send alt, title or caption.' );
		}
		return array( 'id' => $id, 'change_id' => wpu_bt_change_add( 'media_update', 'Updated media #' . $id, array( 'kind' => 'multi', 'items' => $items ) ) );
	},
) );
