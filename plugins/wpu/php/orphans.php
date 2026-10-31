<?php
/**
 * Dangling and empty things a visitor can actually hit.
 *
 *   pwsh bin/wpphp.ps1 php/orphans.php
 */

defined( 'ABSPATH' ) || exit;

function wpsb_sec( string $t ): void {
	echo "\n" . str_repeat( '-', 74 ) . "\n  " . strtoupper( $t ) . "\n" . str_repeat( '-', 74 ) . "\n";
}

/* ---------------- menu items pointing at nothing ---------------- */

wpsb_sec( 'broken menu items' );
$found = 0;

foreach ( wp_get_nav_menus() as $menu ) {
	foreach ( wp_get_nav_menu_items( $menu->term_id ) ?: array() as $item ) {
		$bad = '';

		if ( 'post_type' === $item->type ) {
			$target = get_post( $item->object_id );
			if ( ! $target ) {
				$bad = 'target deleted';
			} elseif ( 'publish' !== $target->post_status ) {
				$bad = 'target is ' . $target->post_status;
			}
		} elseif ( 'taxonomy' === $item->type && ! get_term( $item->object_id ) ) {
			$bad = 'term deleted';
		}

		if ( $bad ) {
			printf( "  %-22s %-30s %s\n", $menu->name, substr( $item->title, 0, 30 ), $bad );
			$found++;
		}
	}
}

if ( ! $found ) {
	echo "  none\n";
}

/* ---------------- published pages with no content ---------------- */

wpsb_sec( 'empty published pages' );
$found = 0;

// WooCommerce's shop/cart/checkout/account pages are rendered by templates and
// legitimately have no post_content of their own.
$functional = array();

if ( function_exists( 'wc_get_page_id' ) ) {
	foreach ( array( 'shop', 'cart', 'checkout', 'myaccount', 'terms' ) as $wc_page ) {
		$id = wc_get_page_id( $wc_page );
		if ( $id > 0 ) {
			$functional[] = $id;
		}
	}
}

// The posts page is rendered by the blog template, not by its own content.
$functional[] = (int) get_option( 'page_for_posts' );

foreach ( get_posts( array( 'post_type' => 'page', 'post_status' => 'publish', 'posts_per_page' => -1 ) ) as $p ) {
	if ( in_array( (int) $p->ID, $functional, true ) ) {
		continue;
	}

	$builder = 'builder' === get_post_meta( $p->ID, '_elementor_edit_mode', true );
	$len     = strlen( trim( wp_strip_all_tags( $p->post_content ) ) );

	// A builder page has its content in postmeta, so an empty post_content is
	// expected there — only flag it if it has no builder data either.
	if ( $builder ) {
		$data = (string) get_post_meta( $p->ID, '_elementor_data', true );
		if ( strlen( $data ) > 40 ) {
			continue;
		}
	}

	// Pages that are only ever a shortcode target are legitimately short.
	if ( $len > 60 || preg_match( '/\[[a-z_]+/i', $p->post_content ) ) {
		continue;
	}

	printf( "  %-6d %-34s /%s/   %d chars\n", $p->ID, substr( $p->post_title, 0, 34 ), $p->post_name, $len );
	$found++;
}

if ( ! $found ) {
	echo "  none\n";
}

/* ---------------- attachments whose file is missing ---------------- */

wpsb_sec( 'missing media files' );
$found = 0;

foreach ( get_posts( array( 'post_type' => 'attachment', 'post_status' => 'inherit', 'posts_per_page' => -1 ) ) as $a ) {
	$file = get_attached_file( $a->ID );

	if ( $file && ! file_exists( $file ) ) {
		printf( "  %-6d %s\n", $a->ID, basename( $file ) );
		$found++;
	}
}

echo $found ? '' : "  none\n";

/* ---------------- products without an image or price ---------------- */

if ( class_exists( 'WooCommerce' ) ) {
	wpsb_sec( 'products missing an image or price' );
	$found = 0;

	foreach ( get_posts( array( 'post_type' => 'product', 'post_status' => 'publish', 'posts_per_page' => -1, 'fields' => 'ids' ) ) as $pid ) {
		$product = wc_get_product( $pid );
		if ( ! $product ) {
			continue;
		}

		$issues = array();
		if ( ! has_post_thumbnail( $pid ) ) {
			$issues[] = 'no image';
		}
		if ( '' === $product->get_price() ) {
			$issues[] = 'no price';
		}

		if ( $issues ) {
			printf( "  %-6d %-38s %s\n", $pid, substr( $product->get_name(), 0, 38 ), implode( ', ', $issues ) );
			$found++;
		}
	}

	echo $found ? '' : "  none\n";
}

echo "\n";
