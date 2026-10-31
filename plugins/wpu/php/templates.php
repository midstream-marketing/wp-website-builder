<?php
/**
 * Read-only inventory of the Elementor library: templates (type, conditions,
 * size), the active kit's global colours and fonts, and media counts.
 *
 *   powershell -File bin/rwpphp.ps1 php/templates.php
 */

defined( 'ABSPATH' ) || exit;

function wpsb_h( string $title ): void {
	echo "\n" . str_repeat( '=', 74 ) . "\n  " . strtoupper( $title ) . "\n" . str_repeat( '=', 74 ) . "\n";
}

wpsb_h( 'elementor library' );
$tpls = get_posts( array(
	'post_type'   => 'elementor_library',
	'post_status' => 'any',
	'numberposts' => -1,
	'orderby'     => 'ID',
	'order'       => 'ASC',
) );
foreach ( $tpls as $t ) {
	$type  = get_post_meta( $t->ID, '_elementor_template_type', true );
	$conds = get_post_meta( $t->ID, '_elementor_conditions', true );
	$data  = get_post_meta( $t->ID, '_elementor_data', true );
	printf(
		"  %-6d %-8s %-14s %-40s %7s chars  %s\n",
		$t->ID,
		$t->post_status,
		$type ?: '?',
		mb_strimwidth( $t->post_title, 0, 40, '…' ),
		number_format( strlen( (string) $data ) ),
		$conds ? 'conditions: ' . implode( ', ', (array) $conds ) : ''
	);
}
printf( "  total: %d\n", count( $tpls ) );

wpsb_h( 'active kit' );
$kit_id = (int) get_option( 'elementor_active_kit' );
printf( "%-24s %d (%s)\n", 'Kit ID', $kit_id, get_the_title( $kit_id ) );
$settings = (array) get_post_meta( $kit_id, '_elementor_page_settings', true );
foreach ( array( 'system_colors', 'custom_colors' ) as $k ) {
	foreach ( (array) ( $settings[ $k ] ?? array() ) as $c ) {
		printf( "  %-7s %-24s %s\n", $k === 'system_colors' ? 'colour' : 'custom', $c['title'] ?? $c['_id'], $c['color'] ?? '' );
	}
}
foreach ( array( 'system_typography', 'custom_typography' ) as $k ) {
	foreach ( (array) ( $settings[ $k ] ?? array() ) as $f ) {
		printf(
			"  %-7s %-24s %s %s\n",
			'font',
			$f['title'] ?? $f['_id'],
			$f['typography_font_family'] ?? '(inherit)',
			$f['typography_font_weight'] ?? ''
		);
	}
}
printf( "%-24s %s\n", 'Site logo', ( $settings['site_logo']['url'] ?? '' ) ?: '(none)' );
printf( "%-24s %s\n", 'Body font', $settings['body_typography_font_family'] ?? '(unset)' );

wpsb_h( 'media' );
$counts = wp_count_attachments();
foreach ( (array) $counts as $mime => $n ) {
	if ( $n ) {
		printf( "  %-30s %d\n", $mime, $n );
	}
}

wpsb_h( 'template kit import' );
foreach ( get_posts( array( 'post_type' => 'envato_tk_import', 'post_status' => 'any', 'numberposts' => -1 ) ) as $k ) {
	printf( "  %-6d %s\n", $k->ID, $k->post_title );
}
