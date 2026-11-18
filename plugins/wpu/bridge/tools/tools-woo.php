<?php
/**
 * WooCommerce: products and variations, orders (status and notes), coupons, a store summary.
 * Everything goes through WooCommerce's own CRUD objects, so its caches, lookups and hooks stay right
 * (and it works with both order storage types). Nothing is ever deleted; refunds are not offered.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

function wpu_bt_has_woo() {
	return class_exists( 'WooCommerce' ) && function_exists( 'wc_get_product' );
}

/** Product fields people change, mapped to WooCommerce props. */
function wpu_bt_woo_product_props() {
	return array(
		'name'               => array( 'type' => 'string' ),
		'status'             => array( 'type' => 'string', 'enum' => array( 'draft', 'pending', 'private', 'publish' ) ),
		'sku'                => array( 'type' => 'string' ),
		'regular_price'      => array( 'type' => 'string', 'description' => 'e.g. "49.00"; "" clears it' ),
		'sale_price'         => array( 'type' => 'string', 'description' => '"" ends the sale' ),
		'date_on_sale_from'  => array( 'type' => 'string', 'description' => 'YYYY-MM-DD or ""' ),
		'date_on_sale_to'    => array( 'type' => 'string', 'description' => 'YYYY-MM-DD or ""' ),
		'manage_stock'       => array( 'type' => 'boolean' ),
		'stock_quantity'     => array( 'type' => 'integer' ),
		'stock_status'       => array( 'type' => 'string', 'enum' => array( 'instock', 'outofstock', 'onbackorder' ) ),
		'description'        => array( 'type' => 'string', 'description' => 'HTML or block markup' ),
		'short_description'  => array( 'type' => 'string' ),
		'categories'         => array( 'type' => 'array', 'items' => array( 'type' => 'string' ), 'description' => 'Category names or ids; replaces the list. Missing names are created.' ),
		'tags'               => array( 'type' => 'array', 'items' => array( 'type' => 'string' ) ),
		'image_id'           => array( 'type' => 'integer', 'description' => 'Media id (media_upload first).' ),
		'gallery_image_ids'  => array( 'type' => 'array', 'items' => array( 'type' => 'integer' ) ),
		'weight'             => array( 'type' => 'string' ),
		'length'             => array( 'type' => 'string' ),
		'width'              => array( 'type' => 'string' ),
		'height'             => array( 'type' => 'string' ),
		'featured'           => array( 'type' => 'boolean' ),
		'catalog_visibility' => array( 'type' => 'string', 'enum' => array( 'visible', 'catalog', 'search', 'hidden' ) ),
		'virtual'            => array( 'type' => 'boolean' ),
	);
}

/** Current values of the editable props (for undo and for reading). */
function wpu_bt_woo_snapshot( WC_Product $p ) {
	$from = $p->get_date_on_sale_from( 'edit' );
	$to   = $p->get_date_on_sale_to( 'edit' );
	return array(
		'name'               => $p->get_name( 'edit' ),
		'status'             => $p->get_status( 'edit' ),
		'sku'                => $p->get_sku( 'edit' ),
		'regular_price'      => $p->get_regular_price( 'edit' ),
		'sale_price'         => $p->get_sale_price( 'edit' ),
		'date_on_sale_from'  => $from ? $from->date( 'Y-m-d' ) : '',
		'date_on_sale_to'    => $to ? $to->date( 'Y-m-d' ) : '',
		'manage_stock'       => $p->get_manage_stock( 'edit' ),
		'stock_quantity'     => $p->get_stock_quantity( 'edit' ),
		'stock_status'       => $p->get_stock_status( 'edit' ),
		'description'        => $p->get_description( 'edit' ),
		'short_description'  => $p->get_short_description( 'edit' ),
		'category_ids'       => $p->get_category_ids( 'edit' ),
		'tag_ids'            => $p->get_tag_ids( 'edit' ),
		'image_id'           => (int) $p->get_image_id( 'edit' ),
		'gallery_image_ids'  => $p->get_gallery_image_ids( 'edit' ),
		'weight'             => $p->get_weight( 'edit' ),
		'length'             => $p->get_length( 'edit' ),
		'width'              => $p->get_width( 'edit' ),
		'height'             => $p->get_height( 'edit' ),
		'featured'           => $p->get_featured( 'edit' ),
		'catalog_visibility' => $p->get_catalog_visibility( 'edit' ),
		'virtual'            => $p->get_virtual( 'edit' ),
	);
}

function wpu_bt_woo_terms( $list, $tax ) {
	$ids = array();
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
			if ( ! current_user_can( 'manage_product_terms' ) ) {
				return wpu_bt_err( 'Term "' . $name . '" does not exist and you cannot create product terms.' );
			}
			$found = wp_insert_term( $name, $tax );
			if ( is_wp_error( $found ) ) {
				return $found;
			}
		}
		$ids[] = (int) ( is_array( $found ) ? $found['term_id'] : $found );
	}
	return $ids;
}

/** Tool args -> WooCommerce props (validated). */
function wpu_bt_woo_props_from_args( array $a, $is_variation ) {
	$props = array();
	$text  = array( 'name', 'sku', 'weight', 'length', 'width', 'height' );
	foreach ( $text as $k ) {
		if ( isset( $a[ $k ] ) ) {
			$props[ $k ] = sanitize_text_field( (string) $a[ $k ] );
		}
	}
	foreach ( array( 'regular_price', 'sale_price' ) as $k ) {
		if ( isset( $a[ $k ] ) ) {
			$v = trim( (string) $a[ $k ] );
			if ( '' !== $v && ! is_numeric( wc_format_decimal( $v ) ) ) {
				return wpu_bt_err( $k . ' must be a number, e.g. "49.00".' );
			}
			$props[ $k ] = '' === $v ? '' : wc_format_decimal( $v );
		}
	}
	foreach ( array( 'date_on_sale_from', 'date_on_sale_to' ) as $k ) {
		if ( isset( $a[ $k ] ) ) {
			$v = trim( (string) $a[ $k ] );
			if ( '' !== $v && ! preg_match( '/^\d{4}-\d{2}-\d{2}$/', $v ) ) {
				return wpu_bt_err( $k . ' must be YYYY-MM-DD.' );
			}
			$props[ $k ] = $v;
		}
	}
	foreach ( array( 'manage_stock', 'featured', 'virtual' ) as $k ) {
		if ( isset( $a[ $k ] ) ) {
			$props[ $k ] = wpu_bt_bool( $a, $k );
		}
	}
	if ( isset( $a['stock_quantity'] ) ) {
		$props['stock_quantity'] = (int) $a['stock_quantity'];
	}
	foreach ( array( 'status', 'stock_status', 'catalog_visibility' ) as $k ) {
		if ( isset( $a[ $k ] ) ) {
			$props[ $k ] = sanitize_key( (string) $a[ $k ] );
		}
	}
	if ( isset( $a['description'] ) ) {
		$props['description'] = wp_kses_post( (string) $a['description'] );
	}
	if ( isset( $a['short_description'] ) ) {
		$props['short_description'] = wp_kses_post( (string) $a['short_description'] );
	}
	if ( ! $is_variation ) {
		if ( isset( $a['categories'] ) ) {
			$ids = wpu_bt_woo_terms( $a['categories'], 'product_cat' );
			if ( is_wp_error( $ids ) ) {
				return $ids;
			}
			$props['category_ids'] = $ids;
		}
		if ( isset( $a['tags'] ) ) {
			$ids = wpu_bt_woo_terms( $a['tags'], 'product_tag' );
			if ( is_wp_error( $ids ) ) {
				return $ids;
			}
			$props['tag_ids'] = $ids;
		}
	} elseif ( isset( $a['categories'] ) || isset( $a['tags'] ) || isset( $a['featured'] ) || isset( $a['catalog_visibility'] ) ) {
		return wpu_bt_err( 'Variations have no categories, tags, featured flag or visibility: change the parent product.' );
	}
	if ( isset( $a['image_id'] ) ) {
		$img = (int) $a['image_id'];
		if ( $img && 'attachment' !== get_post_type( $img ) ) {
			return wpu_bt_err( 'image_id ' . $img . ' is not a media item.' );
		}
		$props['image_id'] = $img;
	}
	if ( isset( $a['gallery_image_ids'] ) ) {
		$ids = array_values( array_filter( array_map( 'intval', (array) $a['gallery_image_ids'] ), function ( $i ) {
			return 'attachment' === get_post_type( $i );
		} ) );
		$props['gallery_image_ids'] = $ids;
	}
	if ( isset( $props['sku'] ) && '' !== $props['sku'] ) {
		$exists = wc_get_product_id_by_sku( $props['sku'] );
		if ( $exists && ( ! isset( $a['id'] ) || (int) $a['id'] !== (int) $exists ) ) {
			return wpu_bt_err( 'SKU ' . $props['sku'] . ' is already used by product #' . $exists . '.' );
		}
	}
	return $props;
}

function wpu_bt_woo_row( WC_Product $p, $full = false ) {
	$row = array(
		'id'            => $p->get_id(),
		'type'          => $p->get_type(),
		'name'          => $p->get_name(),
		'status'        => $p->get_status(),
		'sku'           => $p->get_sku(),
		'price'         => $p->get_price(),
		'regular_price' => $p->get_regular_price(),
		'sale_price'    => $p->get_sale_price(),
		'stock_status'  => $p->get_stock_status(),
		'stock'         => $p->get_manage_stock() ? $p->get_stock_quantity() : null,
		'url'           => $p->get_permalink(),
	);
	if ( $p->get_parent_id() ) {
		$row['parent_id']  = $p->get_parent_id();
		$row['attributes'] = $p->get_attributes();
	} else {
		$row['categories'] = wp_list_pluck( get_the_terms( $p->get_id(), 'product_cat' ) ?: array(), 'name' );
	}
	if ( $p->is_type( 'variable' ) ) {
		$row['variations'] = count( $p->get_children() );
	}
	if ( $full ) {
		$snap                     = wpu_bt_woo_snapshot( $p );
		$row                      = array_merge( $row, $snap );
		$row['total_sales']       = (int) $p->get_total_sales();
		$row['image_url']         = $p->get_image_id() ? wp_get_attachment_url( $p->get_image_id() ) : null;
		$row['tags']              = wp_list_pluck( get_the_terms( $p->get_id(), 'product_tag' ) ?: array(), 'name' );
		if ( ! $p->get_parent_id() ) {
			$attrs = array();
			foreach ( $p->get_attributes() as $key => $attr ) {
				if ( is_object( $attr ) && method_exists( $attr, 'get_options' ) ) {
					$opts = $attr->is_taxonomy() ? wc_get_product_terms( $p->get_id(), $attr->get_name(), array( 'fields' => 'names' ) ) : $attr->get_options();
					$attrs[] = array( 'name' => wc_attribute_label( $attr->get_name() ), 'key' => $key, 'options' => $opts, 'variation' => $attr->get_variation(), 'visible' => $attr->get_visible() );
				}
			}
			$row['attributes'] = $attrs;
		}
		if ( $p->is_type( 'variable' ) ) {
			$vars = array();
			foreach ( array_slice( $p->get_children(), 0, 100 ) as $vid ) {
				$v = wc_get_product( $vid );
				if ( $v ) {
					$vars[] = wpu_bt_woo_row( $v );
				}
			}
			$row['variations'] = $vars;
		}
	}
	return $row;
}

wpu_bt_define_tool( 'woo_products_list', array(
	'title'       => 'List products',
	'description' => 'WooCommerce products with price, sale price, stock and categories. Filter by search text, category, status, type, stock status or SKU.',
	'cap'         => 'edit_products',
	'available'   => 'wpu_bt_has_woo',
	'props'       => array(
		'search'       => array( 'type' => 'string' ),
		'category'     => array( 'type' => 'string', 'description' => 'Category slug' ),
		'status'       => array( 'type' => 'string', 'enum' => array( 'any', 'publish', 'draft', 'pending', 'private' ) ),
		'type'         => array( 'type' => 'string', 'enum' => array( 'simple', 'variable', 'grouped', 'external' ) ),
		'stock_status' => array( 'type' => 'string', 'enum' => array( 'instock', 'outofstock', 'onbackorder' ) ),
		'sku'          => array( 'type' => 'string' ),
		'on_sale'      => array( 'type' => 'boolean' ),
		'per_page'     => array( 'type' => 'integer', 'description' => '1-100, default 30' ),
		'page'         => array( 'type' => 'integer' ),
	),
	'run'         => function ( $a ) {
		$q = array(
			'limit'    => wpu_bt_int( $a, 'per_page', 30, 1, 100 ),
			'page'     => wpu_bt_int( $a, 'page', 1, 1, 10000 ),
			'status'   => isset( $a['status'] ) && 'any' !== $a['status'] ? $a['status'] : array( 'publish', 'draft', 'pending', 'private' ),
			'paginate' => true,
			'orderby'  => 'date',
			'order'    => 'DESC',
		);
		foreach ( array( 'type', 'stock_status', 'sku' ) as $k ) {
			if ( ! empty( $a[ $k ] ) ) {
				$q[ $k ] = sanitize_text_field( (string) $a[ $k ] );
			}
		}
		if ( ! empty( $a['category'] ) ) {
			$q['category'] = array( sanitize_title( (string) $a['category'] ) );
		}
		$include = null;
		if ( ! empty( $a['search'] ) ) {
			$include = WC_Data_Store::load( 'product' )->search_products( wc_clean( (string) $a['search'] ), '', false, true, 500 );
			$include = array_values( array_filter( array_map( 'intval', (array) $include ) ) );
		}
		if ( wpu_bt_bool( $a, 'on_sale' ) ) {
			$sale    = wc_get_product_ids_on_sale();
			$include = null === $include ? $sale : array_values( array_intersect( $include, $sale ) );
		}
		if ( null !== $include ) {
			if ( ! $include ) {
				return array( 'total' => 0, 'items' => array() );
			}
			$q['include'] = $include;
		}
		$res  = wc_get_products( $q );
		$rows = array();
		foreach ( $res->products as $p ) {
			$rows[] = wpu_bt_woo_row( $p );
		}
		return array( 'total' => (int) $res->total, 'pages' => (int) $res->max_num_pages, 'currency' => get_woocommerce_currency(), 'items' => $rows );
	},
) );

wpu_bt_define_tool( 'woo_product_get', array(
	'title'       => 'Get product',
	'description' => 'One product (or variation) in full: prices, sale dates, stock, descriptions, categories, images, attributes and, for a variable product, its variations.',
	'cap'         => 'edit_products',
	'available'   => 'wpu_bt_has_woo',
	'props'       => array( 'id' => array( 'type' => 'integer' ) ),
	'required'    => array( 'id' ),
	'run'         => function ( $a ) {
		$p = wc_get_product( absint( $a['id'] ) );
		if ( ! $p ) {
			return wpu_bt_err( 'No product ' . absint( $a['id'] ) . '.' );
		}
		return wpu_bt_woo_row( $p, true );
	},
) );

wpu_bt_define_tool( 'woo_product_create', array(
	'title'       => 'Create product',
	'description' => 'Create a simple product. It is a draft unless you set status. Returns its id and a change_id (undo moves it to the trash).',
	'cap'         => 'edit_products',
	'available'   => 'wpu_bt_has_woo',
	'props'       => wpu_bt_woo_product_props(),
	'required'    => array( 'name' ),
	'write'       => true,
	'run'         => function ( $a ) {
		if ( isset( $a['status'] ) && 'publish' === $a['status'] && ! current_user_can( 'publish_products' ) ) {
			return wpu_bt_err( 'You cannot publish products.' );
		}
		$props = wpu_bt_woo_props_from_args( $a + array( 'status' => 'draft' ), false );
		if ( is_wp_error( $props ) ) {
			return $props;
		}
		$p   = new WC_Product_Simple();
		$err = $p->set_props( $props );
		if ( is_wp_error( $err ) ) {
			return $err;
		}
		$id = $p->save();
		if ( ! $id ) {
			return wpu_bt_err( 'WooCommerce did not save the product.' );
		}
		$cid = wpu_bt_change_add( 'woo_product_create', 'Created product #' . $id . ' "' . $p->get_name() . '"', array( 'kind' => 'trash', 'id' => $id ) );
		return array( 'product' => wpu_bt_woo_row( $p ), 'edit_url' => get_edit_post_link( $id, 'raw' ), 'change_id' => $cid );
	},
) );

wpu_bt_define_tool( 'woo_product_update', array(
	'title'       => 'Update product',
	'description' => 'Change a product or a variation (use the variation id): name, status, SKU, prices, sale dates, stock, descriptions, categories, tags, images, dimensions. Only fields you send change. Returns a change_id for undo.',
	'cap'         => 'edit_products',
	'available'   => 'wpu_bt_has_woo',
	'props'       => array( 'id' => array( 'type' => 'integer' ) ) + wpu_bt_woo_product_props(),
	'required'    => array( 'id' ),
	'write'       => true,
	'run'         => function ( $a ) {
		$id = absint( $a['id'] );
		$p  = wc_get_product( $id );
		if ( ! $p || ! current_user_can( 'edit_post', $p->get_parent_id() ? $p->get_parent_id() : $id ) ) {
			return wpu_bt_err( 'No product ' . $id . ' that you can edit.' );
		}
		if ( isset( $a['status'] ) && 'publish' === $a['status'] && ! current_user_can( 'publish_products' ) ) {
			return wpu_bt_err( 'You cannot publish products.' );
		}
		$props = wpu_bt_woo_props_from_args( $a, (bool) $p->get_parent_id() );
		if ( is_wp_error( $props ) ) {
			return $props;
		}
		if ( ! $props ) {
			return wpu_bt_err( 'Send at least one field to change.' );
		}
		$snap   = wpu_bt_woo_snapshot( $p );
		$before = array_intersect_key( $snap, $props );
		$err    = $p->set_props( $props );
		if ( is_wp_error( $err ) ) {
			return $err;
		}
		$p->save();
		$changes = array();
		$fresh   = wpu_bt_woo_snapshot( wc_get_product( $id ) );
		foreach ( $before as $k => $v ) {
			if ( $fresh[ $k ] !== $v ) {
				$changes[ $k ] = array( 'from' => $v, 'to' => $fresh[ $k ] );
			}
		}
		$cid = wpu_bt_change_add( 'woo_product_update', 'Product #' . $id . ' "' . $p->get_name() . '": ' . implode( ', ', array_keys( $props ) ), array( 'kind' => 'woo_product', 'id' => $id, 'props' => $before ) );
		return array( 'id' => $id, 'changes' => $changes ? $changes : new stdClass(), 'url' => $p->get_permalink(), 'change_id' => $cid );
	},
) );

function wpu_bt_woo_undo_product( array $p ) {
	if ( ! wpu_bt_has_woo() ) {
		return wpu_bt_err( 'WooCommerce is not active.' );
	}
	$prod = wc_get_product( absint( $p['id'] ) );
	if ( ! $prod ) {
		return wpu_bt_err( 'The product is gone.' );
	}
	$err = $prod->set_props( (array) $p['props'] );
	if ( is_wp_error( $err ) ) {
		return $err;
	}
	$prod->save();
	return array( 'product' => $prod->get_id(), 'restored' => array_keys( (array) $p['props'] ) );
}

/* -------------------------------------------------------------------------
 * Orders
 * ---------------------------------------------------------------------- */

function wpu_bt_woo_order_row( WC_Order $o, $full = false ) {
	$created = $o->get_date_created();
	$row     = array(
		'id'       => $o->get_id(),
		'number'   => $o->get_order_number(),
		'status'   => $o->get_status(),
		'total'    => $o->get_total(),
		'currency' => $o->get_currency(),
		'date'     => $created ? $created->date( 'c' ) : null,
		'customer' => trim( $o->get_formatted_billing_full_name() ),
		'email'    => $o->get_billing_email(),
		'items'    => $o->get_item_count(),
	);
	if ( $full ) {
		$lines = array();
		foreach ( $o->get_items() as $item ) {
			$lines[] = array(
				'name'         => $item->get_name(),
				'quantity'     => $item->get_quantity(),
				'total'        => $item->get_total(),
				'product_id'   => method_exists( $item, 'get_product_id' ) ? $item->get_product_id() : null,
				'variation_id' => method_exists( $item, 'get_variation_id' ) ? $item->get_variation_id() : null,
			);
		}
		$notes = array();
		foreach ( wc_get_order_notes( array( 'order_id' => $o->get_id(), 'limit' => 20 ) ) as $n ) {
			$notes[] = array( 'date' => $n->date_created ? $n->date_created->date( 'c' ) : null, 'note' => wp_strip_all_tags( $n->content ), 'to_customer' => (bool) $n->customer_note, 'by' => $n->added_by );
		}
		$row += array(
			'lines'          => $lines,
			'subtotal'       => $o->get_subtotal(),
			'shipping_total' => $o->get_shipping_total(),
			'discount_total' => $o->get_discount_total(),
			'tax_total'      => $o->get_total_tax(),
			'payment'        => $o->get_payment_method_title(),
			'shipping'       => $o->get_shipping_method(),
			'billing'        => $o->get_address( 'billing' ),
			'shipping_to'    => $o->get_address( 'shipping' ),
			'customer_note'  => $o->get_customer_note(),
			'notes'          => $notes,
			'edit_url'       => $o->get_edit_order_url(),
		);
	}
	return $row;
}

wpu_bt_define_tool( 'woo_orders_list', array(
	'title'       => 'List orders',
	'description' => 'Recent WooCommerce orders with status, total, customer and item count. Filter by status, customer email or dates.',
	'cap'         => 'edit_shop_orders',
	'group'       => 'orders',
	'available'   => 'wpu_bt_has_woo',
	'props'       => array(
		'status'   => array( 'type' => 'string', 'description' => 'e.g. processing, on-hold, completed, pending, cancelled, refunded, failed' ),
		'email'    => array( 'type' => 'string', 'description' => 'Billing email' ),
		'after'    => array( 'type' => 'string', 'description' => 'YYYY-MM-DD' ),
		'before'   => array( 'type' => 'string', 'description' => 'YYYY-MM-DD' ),
		'per_page' => array( 'type' => 'integer', 'description' => '1-100, default 25' ),
		'page'     => array( 'type' => 'integer' ),
	),
	'run'         => function ( $a ) {
		$q = array(
			'limit'    => wpu_bt_int( $a, 'per_page', 25, 1, 100 ),
			'page'     => wpu_bt_int( $a, 'page', 1, 1, 10000 ),
			'paginate' => true,
			'orderby'  => 'date',
			'order'    => 'DESC',
			'type'     => 'shop_order',
		);
		if ( ! empty( $a['status'] ) ) {
			$q['status'] = array( 'wc-' . preg_replace( '/^wc-/', '', sanitize_key( (string) $a['status'] ) ) );
		}
		if ( ! empty( $a['email'] ) ) {
			$q['billing_email'] = sanitize_email( (string) $a['email'] );
		}
		$after  = ! empty( $a['after'] ) && preg_match( '/^\d{4}-\d{2}-\d{2}$/', $a['after'] ) ? $a['after'] : '';
		$before = ! empty( $a['before'] ) && preg_match( '/^\d{4}-\d{2}-\d{2}$/', $a['before'] ) ? $a['before'] : '';
		if ( $after && $before ) {
			$q['date_created'] = $after . '...' . $before;
		} elseif ( $after ) {
			$q['date_created'] = '>=' . $after;
		} elseif ( $before ) {
			$q['date_created'] = '<=' . $before;
		}
		$res  = wc_get_orders( $q );
		$rows = array();
		foreach ( $res->orders as $o ) {
			if ( $o instanceof WC_Order ) {
				$rows[] = wpu_bt_woo_order_row( $o );
			}
		}
		return array( 'total' => (int) $res->total, 'pages' => (int) $res->max_num_pages, 'items' => $rows, 'statuses' => wc_get_order_statuses() );
	},
) );

wpu_bt_define_tool( 'woo_order_get', array(
	'title'       => 'Get order',
	'description' => 'One order in full: lines, totals, payment and shipping method, addresses, customer note and the order notes.',
	'cap'         => 'edit_shop_orders',
	'group'       => 'orders',
	'available'   => 'wpu_bt_has_woo',
	'props'       => array( 'id' => array( 'type' => 'integer' ) ),
	'required'    => array( 'id' ),
	'run'         => function ( $a ) {
		$o = wc_get_order( absint( $a['id'] ) );
		if ( ! $o instanceof WC_Order ) {
			return wpu_bt_err( 'No order ' . absint( $a['id'] ) . '.' );
		}
		return wpu_bt_woo_order_row( $o, true );
	},
) );

wpu_bt_define_tool( 'woo_order_update', array(
	'title'       => 'Update order',
	'description' => 'Change an order\'s status (WooCommerce then sends its normal emails, e.g. "completed") and/or add a note. A note with to_customer true is emailed to the customer. Refunds are not done here. Returns a change_id; undo restores the old status (emails already sent stay sent).',
	'cap'         => 'edit_shop_orders',
	'group'       => 'orders',
	'available'   => 'wpu_bt_has_woo',
	'props'       => array(
		'id'          => array( 'type' => 'integer' ),
		'status'      => array( 'type' => 'string', 'description' => 'processing, on-hold, completed, cancelled, pending, failed' ),
		'note'        => array( 'type' => 'string' ),
		'to_customer' => array( 'type' => 'boolean', 'description' => 'Email the note to the customer. Default false.' ),
	),
	'required'    => array( 'id' ),
	'write'       => true,
	'run'         => function ( $a ) {
		$o = wc_get_order( absint( $a['id'] ) );
		if ( ! $o instanceof WC_Order ) {
			return wpu_bt_err( 'No order ' . absint( $a['id'] ) . '.' );
		}
		$old = $o->get_status();
		$out = array( 'id' => $o->get_id(), 'from' => $old );
		if ( ! empty( $a['status'] ) ) {
			$new = preg_replace( '/^wc-/', '', sanitize_key( (string) $a['status'] ) );
			if ( 'refunded' === $new ) {
				return wpu_bt_err( 'Refunds must be made in wp-admin, where the payment is returned too.' );
			}
			if ( ! array_key_exists( 'wc-' . $new, wc_get_order_statuses() ) ) {
				return wpu_bt_err( 'Unknown status ' . $new . '. Known: ' . implode( ', ', array_map( function ( $s ) {
					return substr( $s, 3 );
				}, array_keys( wc_get_order_statuses() ) ) ) );
			}
			$o->update_status( $new, 'Changed through WPU Bridge by ' . wp_get_current_user()->user_login . '.', true );
			$out['to'] = $new;
		}
		if ( ! empty( $a['note'] ) ) {
			$o->add_order_note( sanitize_textarea_field( (string) $a['note'] ), wpu_bt_bool( $a, 'to_customer' ) ? 1 : 0, true );
			$out['note_added'] = true;
		}
		if ( ! isset( $out['to'] ) && empty( $out['note_added'] ) ) {
			return wpu_bt_err( 'Send status or note.' );
		}
		if ( isset( $out['to'] ) ) {
			$out['change_id'] = wpu_bt_change_add( 'woo_order_update', 'Order #' . $o->get_order_number() . ': ' . $old . ' -> ' . $out['to'], array( 'kind' => 'woo_order', 'id' => $o->get_id(), 'status' => $old ) );
		}
		return $out;
	},
) );

function wpu_bt_woo_undo_order( array $p ) {
	if ( ! wpu_bt_has_woo() ) {
		return wpu_bt_err( 'WooCommerce is not active.' );
	}
	$o = wc_get_order( absint( $p['id'] ) );
	if ( ! $o instanceof WC_Order ) {
		return wpu_bt_err( 'The order is gone.' );
	}
	$o->update_status( sanitize_key( $p['status'] ), 'Status put back through WPU Bridge (undo).', true );
	return array( 'order' => $o->get_id(), 'status' => $p['status'] );
}

/* -------------------------------------------------------------------------
 * Coupons and summary
 * ---------------------------------------------------------------------- */

wpu_bt_define_tool( 'woo_coupons_list', array(
	'title'       => 'List coupons',
	'description' => 'Coupons with type, amount, expiry, usage and status.',
	'cap'         => 'edit_shop_coupons',
	'available'   => 'wpu_bt_has_woo',
	'props'       => array( 'search' => array( 'type' => 'string' ) ),
	'run'         => function ( $a ) {
		$ids = get_posts( array( 'post_type' => 'shop_coupon', 'post_status' => array( 'publish', 'draft', 'pending', 'future' ), 'numberposts' => 200, 'fields' => 'ids', 's' => wpu_bt_str( $a, 'search' ) ) );
		$out = array();
		foreach ( $ids as $id ) {
			$c     = new WC_Coupon( $id );
			$exp   = $c->get_date_expires();
			$out[] = array(
				'id'          => $id,
				'code'        => $c->get_code(),
				'type'        => $c->get_discount_type(),
				'amount'      => $c->get_amount(),
				'expires'     => $exp ? $exp->date( 'Y-m-d' ) : null,
				'used'        => $c->get_usage_count(),
				'usage_limit' => $c->get_usage_limit(),
				'status'      => get_post_status( $id ),
			);
		}
		return array( 'coupons' => $out );
	},
) );

wpu_bt_define_tool( 'woo_coupon_create', array(
	'title'       => 'Create coupon',
	'description' => 'Create a coupon. active false (the default) saves it as a draft that does not work yet; active true makes it usable straight away. Returns a change_id (undo moves it to the trash).',
	'cap'         => 'edit_shop_coupons',
	'available'   => 'wpu_bt_has_woo',
	'props'       => array(
		'code'           => array( 'type' => 'string' ),
		'discount_type'  => array( 'type' => 'string', 'enum' => array( 'percent', 'fixed_cart', 'fixed_product' ) ),
		'amount'         => array( 'type' => 'string' ),
		'expires'        => array( 'type' => 'string', 'description' => 'YYYY-MM-DD' ),
		'usage_limit'    => array( 'type' => 'integer' ),
		'usage_limit_per_user' => array( 'type' => 'integer' ),
		'minimum_amount' => array( 'type' => 'string' ),
		'individual_use' => array( 'type' => 'boolean' ),
		'free_shipping'  => array( 'type' => 'boolean' ),
		'product_ids'    => array( 'type' => 'array', 'items' => array( 'type' => 'integer' ) ),
		'description'    => array( 'type' => 'string' ),
		'active'         => array( 'type' => 'boolean' ),
	),
	'required'    => array( 'code', 'discount_type', 'amount' ),
	'write'       => true,
	'run'         => function ( $a ) {
		$code = wc_format_coupon_code( sanitize_text_field( (string) $a['code'] ) );
		if ( '' === $code || wc_get_coupon_id_by_code( $code ) ) {
			return wpu_bt_err( 'That coupon code is empty or already exists.' );
		}
		$amount = wc_format_decimal( (string) $a['amount'] );
		if ( ! is_numeric( $amount ) || $amount <= 0 || ( 'percent' === $a['discount_type'] && $amount > 100 ) ) {
			return wpu_bt_err( 'amount must be a positive number (percent at most 100).' );
		}
		$c = new WC_Coupon();
		$c->set_code( $code );
		$c->set_discount_type( (string) $a['discount_type'] );
		$c->set_amount( $amount );
		if ( ! empty( $a['expires'] ) ) {
			if ( ! preg_match( '/^\d{4}-\d{2}-\d{2}$/', $a['expires'] ) ) {
				return wpu_bt_err( 'expires must be YYYY-MM-DD.' );
			}
			$c->set_date_expires( $a['expires'] );
		}
		if ( isset( $a['usage_limit'] ) ) {
			$c->set_usage_limit( max( 0, (int) $a['usage_limit'] ) );
		}
		if ( isset( $a['usage_limit_per_user'] ) ) {
			$c->set_usage_limit_per_user( max( 0, (int) $a['usage_limit_per_user'] ) );
		}
		if ( isset( $a['minimum_amount'] ) ) {
			$c->set_minimum_amount( wc_format_decimal( (string) $a['minimum_amount'] ) );
		}
		if ( isset( $a['individual_use'] ) ) {
			$c->set_individual_use( wpu_bt_bool( $a, 'individual_use' ) );
		}
		if ( isset( $a['free_shipping'] ) ) {
			$c->set_free_shipping( wpu_bt_bool( $a, 'free_shipping' ) );
		}
		if ( isset( $a['product_ids'] ) ) {
			$c->set_product_ids( array_values( array_filter( array_map( 'absint', (array) $a['product_ids'] ) ) ) );
		}
		if ( isset( $a['description'] ) ) {
			$c->set_description( sanitize_textarea_field( (string) $a['description'] ) );
		}
		$c->set_status( wpu_bt_bool( $a, 'active' ) ? 'publish' : 'draft' );
		$id = $c->save();
		if ( ! $id ) {
			return wpu_bt_err( 'WooCommerce did not save the coupon.' );
		}
		$cid = wpu_bt_change_add( 'woo_coupon_create', 'Created coupon ' . $code, array( 'kind' => 'trash', 'id' => $id ) );
		return array( 'id' => $id, 'code' => $code, 'status' => get_post_status( $id ), 'change_id' => $cid );
	},
) );

wpu_bt_define_tool( 'woo_store_summary', array(
	'title'       => 'Store summary',
	'description' => 'Sales over the last 7 and 30 days (paid orders), orders waiting to be processed, and products out of stock or low on stock.',
	'cap'         => 'view_woocommerce_reports',
	'available'   => 'wpu_bt_has_woo',
	'run'         => function () {
		$paid = array( 'wc-processing', 'wc-completed', 'wc-on-hold' );
		$sum  = function ( $days ) use ( $paid ) {
			$ids   = wc_get_orders( array( 'status' => $paid, 'type' => 'shop_order', 'limit' => 2000, 'return' => 'ids', 'date_created' => '>=' . gmdate( 'Y-m-d', time() - $days * DAY_IN_SECONDS ) ) );
			$total = 0.0;
			foreach ( $ids as $id ) {
				$o = wc_get_order( $id );
				if ( $o ) {
					$total += (float) $o->get_total();
				}
			}
			return array( 'orders' => count( $ids ), 'revenue' => round( $total, 2 ), 'capped_at_2000' => count( $ids ) >= 2000 );
		};
		$low_amount = function_exists( 'wc_get_low_stock_amount' ) ? null : (int) get_option( 'woocommerce_notify_low_stock_amount', 2 );
		$out_ids    = wc_get_products( array( 'stock_status' => 'outofstock', 'limit' => 50, 'return' => 'ids', 'status' => 'publish' ) );
		$low        = array();
		foreach ( wc_get_products( array( 'manage_stock' => true, 'stock_status' => 'instock', 'limit' => 300, 'status' => 'publish' ) ) as $p ) {
			$threshold = null === $low_amount ? wc_get_low_stock_amount( $p ) : $low_amount;
			if ( null !== $p->get_stock_quantity() && $p->get_stock_quantity() <= $threshold ) {
				$low[] = array( 'id' => $p->get_id(), 'name' => $p->get_name(), 'stock' => $p->get_stock_quantity() );
			}
		}
		$out_of_stock = array();
		foreach ( $out_ids as $id ) {
			$out_of_stock[] = array( 'id' => $id, 'name' => get_the_title( $id ) );
		}
		return array(
			'currency'     => get_woocommerce_currency(),
			'last_7_days'  => $sum( 7 ),
			'last_30_days' => $sum( 30 ),
			'to_process'   => count( wc_get_orders( array( 'status' => array( 'wc-processing' ), 'type' => 'shop_order', 'limit' => 500, 'return' => 'ids' ) ) ),
			'on_hold'      => count( wc_get_orders( array( 'status' => array( 'wc-on-hold' ), 'type' => 'shop_order', 'limit' => 500, 'return' => 'ids' ) ) ),
			'out_of_stock' => $out_of_stock,
			'low_stock'    => array_slice( $low, 0, 50 ),
		);
	},
) );
