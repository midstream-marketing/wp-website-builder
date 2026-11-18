<?php
/**
 * WordPress Abilities API (WordPress 6.9+): list and run the abilities that WordPress core and plugins
 * (WooCommerce, WPForms, AIOSEO, ...) register for AI and automation.
 *
 * Only abilities their plugin chose to expose are offered: show_in_rest, or meta mcp.public. Each run goes
 * through WP_Ability::execute(), which checks the input against the ability's schema and calls the ability's
 * own permission check as the signed-in person. Abilities marked read-only can run through a separate,
 * read-only tool; everything else counts as a change and obeys the bridge's switches. Abilities have no
 * undo, because the bridge cannot know what another plugin's action changed.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

function wpu_bt_abilities_mode() {
	$m = wpu_bt_setting( 'abilities' );
	return in_array( $m, array( 'all', 'readonly', 'off' ), true ) ? $m : 'all';
}

function wpu_bt_has_abilities() {
	return function_exists( 'wp_get_abilities' ) && 'off' !== wpu_bt_abilities_mode();
}

/** Abilities a plugin chose to make available to outside tools. */
function wpu_bt_ability_exposed( $ab ) {
	$meta = $ab->get_meta();
	return ! empty( $meta['show_in_rest'] ) || ! empty( $meta['mcp']['public'] );
}

function wpu_bt_ability_flags( $ab ) {
	$ann = (array) $ab->get_meta_item( 'annotations', array() );
	return array(
		'readonly'    => ! empty( $ann['readonly'] ),
		'destructive' => isset( $ann['destructive'] ) ? (bool) $ann['destructive'] : null,
		'idempotent'  => isset( $ann['idempotent'] ) ? (bool) $ann['idempotent'] : null,
	);
}

function wpu_bt_ability_find( $name ) {
	$name = (string) $name;
	if ( ! preg_match( '/^[a-z0-9-]+\/[a-z0-9-]+$/', $name ) ) {
		return wpu_bt_err( 'Ability names look like "plugin/action".' );
	}
	$ab = wp_get_ability( $name );
	if ( ! $ab || ! wpu_bt_ability_exposed( $ab ) ) {
		return wpu_bt_err( 'No ability called ' . $name . ' is offered to outside tools on this site. See abilities_list.' );
	}
	return $ab;
}

function wpu_bt_ability_execute( $ab, $input, $token = '', $via_readonly_tool = false ) {
	// An ability whose input is an object takes {} when it needs nothing, not "no input".
	$schema = (array) $ab->get_input_schema();
	if ( null === $input && isset( $schema['type'] ) && 'object' === $schema['type'] ) {
		$input = array();
	}
	$write  = ! wpu_bt_ability_flags( $ab )['readonly'];
	$before = wpu_bt_guard_before( $ab->get_name(), $input, $token, $via_readonly_tool );
	if ( is_wp_error( $before ) ) {
		return $before;
	}
	$out = $ab->execute( $input );
	if ( is_wp_error( $out ) ) {
		return $out;
	}
	$res = array( 'ability' => $ab->get_name(), 'result' => $out );
	$cid = $write ? wpu_bt_guard_after( $ab->get_name(), $before, $out ) : '';
	if ( '' !== $cid ) {
		$res['change_id'] = $cid;
	}
	return $res;
}

wpu_bt_define_tool( 'abilities_list', array(
	'title'       => 'List abilities',
	'description' => 'Actions that WordPress and plugins (for example WooCommerce, WPForms, AIOSEO) offer to AI tools through the WordPress Abilities API, with what each one does, whether it only reads, and its argument names. Pass names to get full descriptions and input schemas. Run them with ability_run_readonly or ability_run.',
	'cap'         => 'edit_posts',
	'available'   => 'wpu_bt_has_abilities',
	'props'       => array(
		'search'   => array( 'type' => 'string' ),
		'category' => array( 'type' => 'string' ),
		'plugin'   => array( 'type' => 'string', 'description' => 'Namespace, e.g. woocommerce, core' ),
		'names'    => array( 'type' => 'array', 'items' => array( 'type' => 'string' ), 'description' => 'Exact names to get with full input and output schemas.' ),
	),
	'run'         => function ( $a ) {
		$args = array();
		if ( ! empty( $a['category'] ) ) {
			$args['category'] = sanitize_key( $a['category'] );
		}
		if ( ! empty( $a['plugin'] ) ) {
			$args['namespace'] = sanitize_key( $a['plugin'] );
		}
		$names  = isset( $a['names'] ) ? array_map( 'strval', (array) $a['names'] ) : array();
		$search = strtolower( wpu_bt_str( $a, 'search' ) );
		$mode   = wpu_bt_abilities_mode();
		$out    = array();
		foreach ( wp_get_abilities( $args ) as $name => $ab ) {
			if ( ! wpu_bt_ability_exposed( $ab ) || ( $names && ! in_array( $name, $names, true ) ) ) {
				continue;
			}
			if ( $search && false === strpos( strtolower( $name . ' ' . $ab->get_label() . ' ' . $ab->get_description() ), $search ) ) {
				continue;
			}
			$f   = wpu_bt_ability_flags( $ab );
			$row = array(
				'name'        => $name,
				'label'       => $ab->get_label(),
				'description' => wpu_bt_trim( $ab->get_description(), $names ? 6000 : 300 ),
				'category'    => $ab->get_category(),
				'readonly'    => $f['readonly'],
				'destructive' => $f['destructive'],
				'runnable'    => $f['readonly'] || 'all' === $mode,
			);
			$pol = wpu_bt_guard_policy( $name );
			if ( 'blocked' === $pol['class'] ) {
				$row['runnable'] = false;
				$row['blocked']  = 'Not run through WPU Bridge: ' . $pol['why'] . '.';
			} elseif ( '' !== $pol['builder'] && 'read' !== $pol['class'] && ! wpu_bt_guard_switch() ) {
				$row['runnable'] = false;
				$row['blocked']  = 'Switched off on this site (Tools > WPU Bridge > Builder AI actions).';
			} elseif ( 'confirm' === $pol['class'] ) {
				$row['needs_go_ahead'] = $pol['why'];
			}
			$schema = (array) $ab->get_input_schema();
			if ( $names ) {
				$row['input_schema'] = $schema ? $schema : new stdClass();
			} else {
				// The list stays small: argument names only. Ask for an ability by name to get its full schema.
				$row['input'] = isset( $schema['properties'] ) ? array_keys( (array) $schema['properties'] ) : array();
			}
			if ( $names ) {
				$row['output_schema'] = $ab->get_output_schema() ? $ab->get_output_schema() : new stdClass();
			}
			$out[] = $row;
			if ( count( $out ) >= 200 ) {
				break;
			}
		}
		return array(
			'mode'      => $mode,
			'count'     => count( $out ),
			'abilities' => $out,
			'note'      => 'readonly' === $mode ? 'This site only allows abilities that read.' : '',
		);
	},
) );

wpu_bt_define_tool( 'ability_run_readonly', array(
	'title'       => 'Run a read-only ability',
	'description' => 'Run an ability that its plugin marked as read-only (it looks things up and changes nothing). input must match the ability\'s input schema. The ability checks your permissions itself.',
	'cap'         => 'edit_posts',
	'available'   => 'wpu_bt_has_abilities',
	'props'       => array(
		'name'  => array( 'type' => 'string', 'description' => 'e.g. core/get-site-info' ),
		'input' => array( 'description' => 'The ability\'s input (object, value or omitted).' ),
	),
	'required'    => array( 'name' ),
	'run'         => function ( $a ) {
		$ab = wpu_bt_ability_find( $a['name'] );
		if ( is_wp_error( $ab ) ) {
			return $ab;
		}
		if ( ! wpu_bt_ability_flags( $ab )['readonly'] ) {
			return wpu_bt_err( $ab->get_name() . ' is not marked read-only by its plugin. Use ability_run, which counts as a change.' );
		}
		return wpu_bt_ability_execute( $ab, array_key_exists( 'input', $a ) ? $a['input'] : null, '', true );
	},
) );

wpu_bt_define_tool( 'ability_run', array(
	'title'       => 'Run an ability',
	'description' => 'Run any ability offered on this site, including ones that change things (create a form entry, update an order, run a plugin action). input must match its input schema; the ability checks your permissions itself. Page-builder abilities (Breakdance, Oxygen, SeedProd) only change things when the site admin has switched that on, and are checked first: code, scripts, embeds and dynamic data are refused, some are blocked, and anything live or site-wide is refused with a confirm_token that you may send back only after the person agreed. Changes to a page return a change_id for undo. Other plugins\' abilities have no undo: say what will happen before running one that is not read-only.',
	'cap'         => 'edit_posts',
	'available'   => function () {
		return wpu_bt_has_abilities() && 'all' === wpu_bt_abilities_mode();
	},
	'props'       => array(
		'name'    => array( 'type' => 'string' ),
		'input'   => array( 'description' => 'The ability\'s input (object, value or omitted).' ),
		'confirm_token' => array( 'type' => 'string', 'description' => 'The code a refused live or site-wide change gave you. Send it only after the person agreed to that exact change.' ),
	),
	'required'    => array( 'name' ),
	'write'       => true,
	'destructive' => true,
	'run'         => function ( $a ) {
		$ab = wpu_bt_ability_find( $a['name'] );
		if ( is_wp_error( $ab ) ) {
			return $ab;
		}
		$res = wpu_bt_ability_execute( $ab, array_key_exists( 'input', $a ) ? $a['input'] : null, wpu_bt_str( $a, 'confirm_token' ) );
		if ( ! is_wp_error( $res ) && empty( $res['change_id'] ) ) {
			$res['note'] = 'No undo for this one: it was another plugin\'s action, or it changed something site-wide.';
		}
		return $res;
	},
) );
