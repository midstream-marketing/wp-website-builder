<?php
/**
 * Every public URL on the site, grouped by type, as JSON - the list the audits
 * (seo.mjs, linkmap.mjs, responsive.mjs) work through.
 *
 *   powershell -File scripts/rinventory.ps1            (runs this and saves sites/<slug>/shots/url-inventory.json)
 *
 * READ ONLY. Published content only; drafts and private posts are left out
 * because a crawler never sees them.
 */
defined( 'ABSPATH' ) || exit;

$out = array( 'site' => home_url( '/' ), 'generated' => gmdate( 'c' ), 'types' => array() );

$types = get_post_types( array( 'public' => true ), 'names' );
unset( $types['attachment'] );
foreach ( $types as $type ) {
	$ids = get_posts( array(
		'post_type'      => $type,
		'post_status'    => 'publish',
		'posts_per_page' => 2000,
		'fields'         => 'ids',
		'orderby'        => 'menu_order title',
		'order'          => 'ASC',
	) );
	foreach ( $ids as $id ) {
		$out['types'][ $type ][] = array(
			'id'    => (int) $id,
			'url'   => get_permalink( $id ),
			'title' => html_entity_decode( get_the_title( $id ), ENT_QUOTES, 'UTF-8' ),
		);
	}
}

foreach ( get_taxonomies( array( 'public' => true ), 'names' ) as $tax ) {
	if ( 'post_format' === $tax ) {
		continue;
	}
	$terms = get_terms( array( 'taxonomy' => $tax, 'hide_empty' => true, 'number' => 500 ) );
	if ( is_wp_error( $terms ) ) {
		continue;
	}
	foreach ( $terms as $t ) {
		$link = get_term_link( $t );
		if ( is_wp_error( $link ) ) {
			continue;
		}
		$out['types'][ 'tax:' . $tax ][] = array( 'id' => (int) $t->term_id, 'url' => $link, 'title' => $t->name );
	}
}

echo wp_json_encode( $out, JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT );
