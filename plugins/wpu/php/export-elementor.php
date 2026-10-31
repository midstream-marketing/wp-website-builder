<?php
/**
 * Read-only backup of every Elementor library post and every Elementor page:
 * title, type, status, _elementor_data, _elementor_page_settings, conditions.
 * Prints one JSON document - redirect it to a local file.
 *
 *   powershell -File bin/rwpphp.ps1 php/export-elementor.php > backups/<site>-elementor-<date>.json
 */

defined( 'ABSPATH' ) || exit;

$posts = get_posts( array(
	'post_type'   => array( 'elementor_library', 'page' ),
	'post_status' => 'any',
	'numberposts' => -1,
) );

$out = array(
	'site'        => home_url(),
	'exported'    => gmdate( 'c' ),
	'active_kit'  => (int) get_option( 'elementor_active_kit' ),
	'options'     => array(
		'show_on_front' => get_option( 'show_on_front' ),
		'page_on_front' => get_option( 'page_on_front' ),
		'blogname'      => get_option( 'blogname' ),
		'permalinks'    => get_option( 'permalink_structure' ),
		'blog_public'   => get_option( 'blog_public' ),
	),
	'posts'       => array(),
);

foreach ( $posts as $p ) {
	$out['posts'][] = array(
		'ID'            => $p->ID,
		'post_type'     => $p->post_type,
		'post_title'    => $p->post_title,
		'post_name'     => $p->post_name,
		'post_status'   => $p->post_status,
		'template_type' => get_post_meta( $p->ID, '_elementor_template_type', true ),
		'conditions'    => get_post_meta( $p->ID, '_elementor_conditions', true ),
		'page_template' => get_post_meta( $p->ID, '_wp_page_template', true ),
		'data'          => get_post_meta( $p->ID, '_elementor_data', true ),
		'settings'      => get_post_meta( $p->ID, '_elementor_page_settings', true ),
	);
}

echo "\n===JSON===\n" . wp_json_encode( $out ) . "\n===END===\n";
