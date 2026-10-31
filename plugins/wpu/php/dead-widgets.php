<?php
/**
 * Find page-builder widgets whose plugin is no longer installed.
 *
 * Elementor renders NOTHING for an unregistered widget type — no error, no
 * placeholder, just a silent empty gap where a section used to be. This is the
 * usual cause of "the page has a big blank space" after a theme or plugin has
 * been swapped.
 *
 *   pwsh bin/wpphp.ps1 php/dead-widgets.php
 */

defined( 'ABSPATH' ) || exit;

if ( ! class_exists( '\Elementor\Plugin' ) ) {
	echo "Elementor is not active — nothing to check.\n";
	return;
}

global $wpdb;

$registered = array_keys( \Elementor\Plugin::$instance->widgets_manager->get_widget_types() );
printf( "%d widget types registered\n\n", count( $registered ) );

$rows = $wpdb->get_results(
	"SELECT post_id, meta_value FROM {$wpdb->postmeta} WHERE meta_key = '_elementor_data'"
);

$live    = array();
$trashed = array();
$totals  = array();

foreach ( $rows as $row ) {
	$post = get_post( $row->post_id );

	if ( ! $post ) {
		continue;
	}

	preg_match_all( '/"widgetType":"([^"]+)"/', $row->meta_value, $m );

	$dead = array();

	foreach ( array_count_values( $m[1] ) as $type => $n ) {
		if ( ! in_array( $type, $registered, true ) ) {
			$dead[]            = "$type x$n";
			$totals[ $type ]   = ( $totals[ $type ] ?? 0 ) + $n;
		}
	}

	if ( ! $dead ) {
		continue;
	}

	$line = sprintf(
		"  %-30s %-18s %s\n",
		substr( $post->post_title, 0, 30 ),
		$post->post_type . '/' . $post->post_status,
		implode( ', ', array_slice( $dead, 0, 6 ) ) . ( count( $dead ) > 6 ? ' …' : '' )
	);

	/*
	 * "Live" means a visitor can actually land on it. Builder template CPTs
	 * (medova_header, elementor_library, and friends) are published but are
	 * only rendered where they have been assigned — listing them as live
	 * buries the pages that genuinely matter.
	 */
	$type_obj = get_post_type_object( $post->post_type );
	$public   = $type_obj && $type_obj->public && $type_obj->publicly_queryable;

	if ( 'publish' === $post->post_status && $public ) {
		$live[] = $line;
	} else {
		$trashed[] = $line;
	}
}

echo str_repeat( '=', 74 ) . "\n  LIVE PAGES WITH DEAD WIDGETS  (these render as blank gaps)\n" . str_repeat( '=', 74 ) . "\n";
echo $live ? implode( '', $live ) : "  none\n";

echo "\n" . str_repeat( '=', 74 ) . "\n  DRAFTS / TRASH / REVISIONS  (not reachable — DB bloat only)\n" . str_repeat( '=', 74 ) . "\n";
printf( "  %d entries\n", count( $trashed ) );

if ( $totals ) {
	arsort( $totals );
	echo "\nMissing widget types, most used first:\n";
	foreach ( array_slice( $totals, 0, 25, true ) as $type => $n ) {
		printf( "  %-42s %d\n", $type, $n );
	}
	echo "\nEach of these is a section that renders as nothing. Either reinstall the\n";
	echo "plugin that provided them, or rebuild those sections with live widgets.\n";
}

echo "\n";
