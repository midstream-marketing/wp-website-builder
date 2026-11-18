<?php
/**
 * Advanced Custom Fields: field groups, reading and writing values on posts, terms, users and the
 * options page, with a type check per field and undo.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

function wpu_bt_has_acf() {
	return function_exists( 'acf_get_field_groups' ) && function_exists( 'update_field' );
}

/**
 * ACF object id from tool input: 123 (post), "term_12", "user_3" or "option". Checks the right capability.
 * @return string|int|WP_Error
 */
function wpu_bt_acf_target( $raw ) {
	if ( is_int( $raw ) || ( is_string( $raw ) && ctype_digit( $raw ) ) ) {
		$id = (int) $raw;
		if ( ! get_post( $id ) || ! current_user_can( 'edit_post', $id ) ) {
			return wpu_bt_err( 'No post ' . $id . ' that you can edit.' );
		}
		return $id;
	}
	$raw = (string) $raw;
	if ( in_array( $raw, array( 'option', 'options' ), true ) ) {
		return current_user_can( 'manage_options' ) ? 'option' : wpu_bt_err( 'Options need an administrator.' );
	}
	if ( preg_match( '/^term_(\d+)$/', $raw, $m ) ) {
		return get_term( (int) $m[1] ) && current_user_can( 'edit_term', (int) $m[1] ) ? 'term_' . (int) $m[1] : wpu_bt_err( 'No term ' . $m[1] . ' that you can edit.' );
	}
	if ( preg_match( '/^user_(\d+)$/', $raw, $m ) ) {
		return get_userdata( (int) $m[1] ) && current_user_can( 'edit_user', (int) $m[1] ) ? 'user_' . (int) $m[1] : wpu_bt_err( 'No user ' . $m[1] . ' that you can edit.' );
	}
	return wpu_bt_err( 'object must be a post id, "term_<id>", "user_<id>" or "option".' );
}

function wpu_bt_acf_field_info( array $f ) {
	$row = array(
		'key'      => $f['key'],
		'name'     => $f['name'],
		'label'    => $f['label'],
		'type'     => $f['type'],
		'required' => ! empty( $f['required'] ),
	);
	if ( ! empty( $f['instructions'] ) ) {
		$row['instructions'] = substr( wp_strip_all_tags( $f['instructions'] ), 0, 200 );
	}
	if ( ! empty( $f['choices'] ) ) {
		$row['choices'] = $f['choices'];
	}
	foreach ( array( 'min', 'max', 'multiple', 'return_format', 'post_type', 'taxonomy', 'display_format' ) as $k ) {
		if ( isset( $f[ $k ] ) && '' !== $f[ $k ] && array() !== $f[ $k ] ) {
			$row[ $k ] = $f[ $k ];
		}
	}
	if ( ! empty( $f['sub_fields'] ) ) {
		$row['sub_fields'] = array_map( 'wpu_bt_acf_field_info', $f['sub_fields'] );
	}
	if ( ! empty( $f['layouts'] ) ) {
		$row['layouts'] = array();
		foreach ( $f['layouts'] as $l ) {
			$row['layouts'][] = array(
				'name'       => $l['name'],
				'label'      => $l['label'],
				'sub_fields' => array_map( 'wpu_bt_acf_field_info', isset( $l['sub_fields'] ) ? $l['sub_fields'] : array() ),
			);
		}
	}
	return $row;
}

/** Validate and clean one value for its field type. @return mixed|WP_Error */
function wpu_bt_acf_value( array $f, $v ) {
	$name = $f['name'];
	$bad  = function ( $msg ) use ( $name ) {
		return wpu_bt_err( 'Field ' . $name . ': ' . $msg );
	};
	if ( null === $v ) {
		return null; // clear the field
	}
	switch ( $f['type'] ) {
		case 'text':
			return sanitize_text_field( (string) $v );
		case 'textarea':
			return sanitize_textarea_field( (string) $v );
		case 'wysiwyg':
			return wp_kses_post( (string) $v );
		case 'email':
			$e = sanitize_email( (string) $v );
			return '' === $e || is_email( $e ) ? $e : $bad( 'not an email address' );
		case 'url':
		case 'oembed':
		case 'page_link':
			if ( is_numeric( $v ) && 'page_link' === $f['type'] ) {
				return get_post( (int) $v ) ? (int) $v : $bad( 'no such post' );
			}
			$u = esc_url_raw( (string) $v, array( 'http', 'https', 'mailto', 'tel' ) );
			return '' === $u && '' !== trim( (string) $v ) ? $bad( 'not a web address' ) : $u;
		case 'number':
		case 'range':
			if ( '' === $v ) {
				return '';
			}
			if ( ! is_numeric( $v ) ) {
				return $bad( 'must be a number' );
			}
			if ( isset( $f['min'] ) && '' !== $f['min'] && $v < $f['min'] ) {
				return $bad( 'below the minimum ' . $f['min'] );
			}
			if ( isset( $f['max'] ) && '' !== $f['max'] && $v > $f['max'] ) {
				return $bad( 'above the maximum ' . $f['max'] );
			}
			return $v + 0;
		case 'true_false':
			return filter_var( $v, FILTER_VALIDATE_BOOLEAN ) ? 1 : 0;
		case 'select':
		case 'radio':
		case 'button_group':
		case 'checkbox':
			$choices = isset( $f['choices'] ) ? array_map( 'strval', array_keys( (array) $f['choices'] ) ) : array();
			$multi   = 'checkbox' === $f['type'] || ! empty( $f['multiple'] );
			$list    = is_array( $v ) ? array_map( 'strval', $v ) : array( (string) $v );
			if ( ! $multi && count( $list ) > 1 ) {
				return $bad( 'takes one value' );
			}
			foreach ( $list as $item ) {
				if ( $choices && ! in_array( $item, $choices, true ) && empty( $f['allow_custom'] ) && empty( $f['other_choice'] ) ) {
					return $bad( '"' . $item . '" is not one of ' . implode( ', ', $choices ) );
				}
			}
			return $multi ? array_map( 'sanitize_text_field', $list ) : sanitize_text_field( $list[0] );
		case 'image':
		case 'file':
			$id = (int) ( is_array( $v ) && isset( $v['id'] ) ? $v['id'] : $v );
			return 0 === $id || 'attachment' === get_post_type( $id ) ? $id : $bad( 'not a media id' );
		case 'gallery':
			$ids = array();
			foreach ( (array) $v as $i ) {
				if ( 'attachment' !== get_post_type( (int) $i ) ) {
					return $bad( (int) $i . ' is not a media id' );
				}
				$ids[] = (int) $i;
			}
			return $ids;
		case 'post_object':
		case 'relationship':
			$ids = array();
			foreach ( (array) $v as $i ) {
				if ( ! get_post( (int) $i ) ) {
					return $bad( 'no post ' . (int) $i );
				}
				$ids[] = (int) $i;
			}
			return ( 'post_object' === $f['type'] && empty( $f['multiple'] ) ) ? ( $ids ? $ids[0] : 0 ) : $ids;
		case 'taxonomy':
			$ids = array();
			foreach ( (array) $v as $i ) {
				if ( ! get_term( (int) $i ) ) {
					return $bad( 'no term ' . (int) $i );
				}
				$ids[] = (int) $i;
			}
			return $ids;
		case 'user':
			$ids = array();
			foreach ( (array) $v as $i ) {
				if ( ! get_userdata( (int) $i ) ) {
					return $bad( 'no user ' . (int) $i );
				}
				$ids[] = (int) $i;
			}
			return empty( $f['multiple'] ) ? ( $ids ? $ids[0] : 0 ) : $ids;
		case 'date_picker':
			$s = preg_replace( '/\D/', '', (string) $v );
			return '' === $s || 8 === strlen( $s ) ? $s : $bad( 'use YYYYMMDD or YYYY-MM-DD' );
		case 'date_time_picker':
			$ts = strtotime( (string) $v );
			return '' === (string) $v ? '' : ( $ts ? gmdate( 'Y-m-d H:i:s', $ts ) : $bad( 'not a date and time' ) );
		case 'time_picker':
			return preg_match( '/^\d{2}:\d{2}(:\d{2})?$/', (string) $v ) || '' === (string) $v ? (string) $v : $bad( 'use HH:MM or HH:MM:SS' );
		case 'color_picker':
			$s = (string) $v;
			return '' === $s || sanitize_hex_color( $s ) || preg_match( '/^rgba?\([\d\s.,%]+\)$/', $s ) ? $s : $bad( 'not a colour' );
		case 'link':
			if ( is_string( $v ) ) {
				return esc_url_raw( $v, array( 'http', 'https', 'mailto', 'tel' ) );
			}
			$v = (array) $v;
			return array(
				'url'    => isset( $v['url'] ) ? esc_url_raw( (string) $v['url'], array( 'http', 'https', 'mailto', 'tel' ) ) : '',
				'title'  => isset( $v['title'] ) ? sanitize_text_field( (string) $v['title'] ) : '',
				'target' => isset( $v['target'] ) && '_blank' === $v['target'] ? '_blank' : '',
			);
		case 'google_map':
			if ( ! is_array( $v ) || ! isset( $v['lat'], $v['lng'] ) || ! is_numeric( $v['lat'] ) || ! is_numeric( $v['lng'] ) ) {
				return $bad( 'must be an object with address, lat and lng' );
			}
			return array( 'address' => sanitize_text_field( isset( $v['address'] ) ? (string) $v['address'] : '' ), 'lat' => (float) $v['lat'], 'lng' => (float) $v['lng'] );
		case 'group':
			return is_array( $v ) ? wpu_bt_acf_row( $f, isset( $f['sub_fields'] ) ? (array) $f['sub_fields'] : array(), $v ) : $bad( 'must be an object of sub-field values' );
		case 'repeater':
			if ( ! is_array( $v ) || ( $v && array_keys( $v ) !== range( 0, count( $v ) - 1 ) ) ) {
				return $bad( 'must be a list of rows' );
			}
			$rows = array();
			foreach ( $v as $i => $row ) {
				$r = is_array( $row ) ? wpu_bt_acf_row( $f, isset( $f['sub_fields'] ) ? (array) $f['sub_fields'] : array(), $row ) : $bad( 'row ' . $i . ' must be an object' );
				if ( is_wp_error( $r ) ) {
					return $r;
				}
				$rows[] = $r;
			}
			return $rows;
		case 'flexible_content':
			if ( ! is_array( $v ) || ( $v && array_keys( $v ) !== range( 0, count( $v ) - 1 ) ) ) {
				return $bad( 'must be a list of rows' );
			}
			$rows = array();
			foreach ( $v as $i => $row ) {
				$layout = is_array( $row ) && isset( $row['acf_fc_layout'] ) ? (string) $row['acf_fc_layout'] : '';
				$subs   = null;
				foreach ( isset( $f['layouts'] ) ? (array) $f['layouts'] : array() as $l ) {
					if ( isset( $l['name'] ) && $l['name'] === $layout ) {
						$subs = isset( $l['sub_fields'] ) ? (array) $l['sub_fields'] : array();
					}
				}
				if ( null === $subs ) {
					return $bad( 'row ' . $i . ' needs "acf_fc_layout" set to one of its layouts' );
				}
				unset( $row['acf_fc_layout'] );
				$r = wpu_bt_acf_row( $f, $subs, $row );
				if ( is_wp_error( $r ) ) {
					return $r;
				}
				$rows[] = array( 'acf_fc_layout' => $layout ) + $r;
			}
			return $rows;
		case 'password':
			return $bad( 'password fields are not changed through the bridge' );
		case 'message':
		case 'tab':
		case 'accordion':
			return $bad( 'this field type holds no value' );
	}
	// Field types from add-ons: plain text only.
	return is_array( $v ) ? $bad( 'this field type (' . $f['type'] . ') only takes text through the bridge' ) : sanitize_text_field( (string) $v );
}

/** Check one row of sub-field values (keyed by sub-field name or key) against the sub-fields' own types. */
function wpu_bt_acf_row( array $parent, array $subs, array $row ) {
	$out = array();
	foreach ( $row as $k => $val ) {
		$sf = null;
		foreach ( $subs as $s ) {
			if ( ( isset( $s['name'] ) && $s['name'] === $k ) || ( isset( $s['key'] ) && $s['key'] === $k ) ) {
				$sf = $s;
				break;
			}
		}
		if ( ! $sf ) {
			return wpu_bt_err( 'Field ' . $parent['name'] . ': unknown sub-field "' . $k . '".' );
		}
		$clean = wpu_bt_acf_value( $sf, $val );
		if ( is_wp_error( $clean ) ) {
			return $clean;
		}
		$out[ $sf['key'] ] = $clean;
	}
	return $out;
}

wpu_bt_define_tool( 'acf_field_groups', array(
	'title'       => 'ACF field groups',
	'description' => 'Advanced Custom Fields groups and their fields (name, key, type, choices, sub-fields). Give a post id or post type to see only the groups that apply to it.',
	'cap'         => 'edit_posts',
	'available'   => 'wpu_bt_has_acf',
	'props'       => array(
		'post_id'   => array( 'type' => 'integer' ),
		'post_type' => array( 'type' => 'string' ),
	),
	'run'         => function ( $a ) {
		$filter = array();
		if ( ! empty( $a['post_id'] ) ) {
			$filter['post_id'] = absint( $a['post_id'] );
		} elseif ( ! empty( $a['post_type'] ) ) {
			$filter['post_type'] = sanitize_key( $a['post_type'] );
		}
		$out = array();
		foreach ( acf_get_field_groups( $filter ) as $g ) {
			$out[] = array(
				'key'      => $g['key'],
				'title'    => $g['title'],
				'active'   => ! empty( $g['active'] ),
				'location' => $g['location'],
				'fields'   => array_map( 'wpu_bt_acf_field_info', (array) acf_get_fields( $g ) ),
			);
		}
		return array( 'groups' => $out );
	},
) );

wpu_bt_define_tool( 'acf_get', array(
	'title'       => 'Get ACF values',
	'description' => 'Custom field values for a post id, "term_<id>", "user_<id>" or "option": every field (or the ones you name) with its type and the raw stored value. Image and file fields also give the address.',
	'cap'         => 'edit_posts',
	'available'   => 'wpu_bt_has_acf',
	'props'       => array(
		'object' => array( 'type' => 'string', 'description' => 'Post id, term_<id>, user_<id> or option' ),
		'fields' => array( 'type' => 'array', 'items' => array( 'type' => 'string' ), 'description' => 'Field names or keys; default all.' ),
	),
	'required'    => array( 'object' ),
	'run'         => function ( $a ) {
		$target = wpu_bt_acf_target( $a['object'] );
		if ( is_wp_error( $target ) ) {
			return $target;
		}
		$objs = get_field_objects( $target, false, true );
		$want = isset( $a['fields'] ) ? array_map( 'strval', (array) $a['fields'] ) : array();
		$out  = array();
		foreach ( (array) $objs as $name => $f ) {
			if ( $want && ! in_array( $name, $want, true ) && ! in_array( $f['key'], $want, true ) ) {
				continue;
			}
			if ( 'password' === $f['type'] ) {
				$f['value'] = '' === (string) $f['value'] ? '' : '[hidden]';
			}
			$row = array( 'name' => $name, 'key' => $f['key'], 'type' => $f['type'], 'label' => $f['label'], 'value' => $f['value'] );
			if ( in_array( $f['type'], array( 'image', 'file' ), true ) && is_numeric( $f['value'] ) && $f['value'] ) {
				$row['url'] = wp_get_attachment_url( (int) $f['value'] );
			}
			$out[] = $row;
		}
		return array( 'object' => $target, 'fields' => $out, 'note' => $out ? '' : 'No ACF fields have values here, or no field group applies. See acf_field_groups.' );
	},
) );

wpu_bt_define_tool( 'acf_update', array(
	'title'       => 'Update ACF values',
	'description' => 'Set custom field values on a post id, "term_<id>", "user_<id>" or "option": {"values":{"field_name":value}}. Each value is checked against its field type (choices, numbers, media and post ids). Repeaters take a list of rows of sub-field names, groups an object. null clears a field. Returns a change_id for undo.',
	'cap'         => 'edit_posts',
	'available'   => 'wpu_bt_has_acf',
	'props'       => array(
		'object' => array( 'type' => 'string', 'description' => 'Post id, term_<id>, user_<id> or option' ),
		'values' => array( 'type' => 'object' ),
	),
	'required'    => array( 'object', 'values' ),
	'write'       => true,
	'run'         => function ( $a ) {
		$target = wpu_bt_acf_target( $a['object'] );
		if ( is_wp_error( $target ) ) {
			return $target;
		}
		$values = (array) $a['values'];
		if ( ! $values || count( $values ) > 100 ) {
			return wpu_bt_err( 'Send 1 to 100 field values.' );
		}
		// Check every value first; write nothing if any is wrong.
		$plan = array();
		foreach ( $values as $sel => $v ) {
			$f = get_field_object( (string) $sel, $target, false, false );
			if ( ! $f ) {
				$f = acf_get_field( (string) $sel );
			}
			if ( ! $f || empty( $f['key'] ) ) {
				return wpu_bt_err( 'Unknown field "' . $sel . '" for ' . $target . '. See acf_field_groups.' );
			}
			$clean = wpu_bt_acf_value( $f, $v );
			if ( is_wp_error( $clean ) ) {
				return $clean;
			}
			$plan[] = array( $f, $clean );
		}
		$before  = array();
		$written = array();
		foreach ( $plan as list( $f, $clean ) ) {
			$old                  = get_field( $f['key'], $target, false );
			$before[ $f['key'] ]  = $old;
			if ( null === $clean ) {
				delete_field( $f['key'], $target );
			} else {
				update_field( $f['key'], $clean, $target );
			}
			$written[] = $f['name'];
		}
		if ( is_int( $target ) ) {
			clean_post_cache( $target );
		}
		$cid = wpu_bt_change_add( 'acf_update', 'ACF on ' . $target . ': ' . implode( ', ', $written ), array( 'kind' => 'acf', 'object' => $target, 'values' => $before ) );
		return array( 'object' => $target, 'updated' => $written, 'change_id' => $cid );
	},
) );

function wpu_bt_acf_undo( array $p ) {
	if ( ! wpu_bt_has_acf() ) {
		return wpu_bt_err( 'ACF is not active.' );
	}
	$target = wpu_bt_acf_target( $p['object'] );
	if ( is_wp_error( $target ) ) {
		return $target;
	}
	foreach ( (array) $p['values'] as $key => $old ) {
		if ( null === $old || '' === $old ) {
			delete_field( $key, $target );
		} else {
			update_field( $key, $old, $target );
		}
	}
	return array( 'object' => $target, 'restored' => array_keys( (array) $p['values'] ) );
}
