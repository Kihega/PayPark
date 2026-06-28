<?php

namespace Tests\Feature;

use App\Models\DeliveryAgency;
use App\Models\FishStock;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class OrderTest extends TestCase
{
    use RefreshDatabase;

    public function test_buyer_can_place_order_with_sellers_own_agency(): void
    {
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10]);
        $agency = DeliveryAgency::factory()->create(['seller_id' => $seller->id]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
            'agency_id' => $agency->id,
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('seller_id', $seller->id)
            ->assertJsonPath('delivery.agency_id', $agency->id);
    }

    public function test_order_rejected_when_agency_belongs_to_a_different_seller(): void
    {
        // Regression test: agency_id was only checked against
        // 'exists:delivery_agencies,id' (anywhere), not against the
        // seller actually being ordered from.
        $seller = User::factory()->seller()->create();
        $otherSeller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10]);
        $otherSellerAgency = DeliveryAgency::factory()->create(['seller_id' => $otherSeller->id]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
            'agency_id' => $otherSellerAgency->id,
        ]);

        $response->assertStatus(422);
    }

    public function test_order_rejected_when_stock_belongs_to_a_different_seller(): void
    {
        $seller = User::factory()->seller()->create();
        $otherSeller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $otherSellerStock = FishStock::factory()->create(['seller_id' => $otherSeller->id, 'quantity_kg' => 10]);
        $agency = DeliveryAgency::factory()->create(['seller_id' => $seller->id]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $otherSellerStock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
            'agency_id' => $agency->id,
        ]);

        $response->assertStatus(422);
    }

    public function test_order_rejected_when_agency_is_inactive(): void
    {
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10]);
        $inactiveAgency = DeliveryAgency::factory()->create(['seller_id' => $seller->id, 'is_active' => false]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
            'agency_id' => $inactiveAgency->id,
        ]);

        $response->assertStatus(422);
    }

    public function test_order_rejected_when_quantity_exceeds_available_stock(): void
    {
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 1]);
        $agency = DeliveryAgency::factory()->create(['seller_id' => $seller->id]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 5]],
            'payment_method' => 'mobile',
            'agency_id' => $agency->id,
        ]);

        $response->assertStatus(422);
    }

    public function test_newly_added_stock_appears_on_the_seller_public_page(): void
    {
        // Covers the "stocks load successfully on the buyer platform"
        // path end-to-end: a seller creates a stock, and it must show
        // up via the same public endpoint the buyer-facing SellerPage
        // calls (GET /sellers/{id}).
        $seller = User::factory()->seller()->create();

        $createResponse = $this->actingAs($seller, 'sanctum')->postJson('/api/stocks', [
            'fish_name' => 'Fresh Tilapia',
            'quantity_kg' => 20,
            'price_per_kg' => 5000,
        ]);
        $createResponse->assertStatus(201);

        $publicResponse = $this->getJson("/api/sellers/{$seller->id}");

        $publicResponse->assertStatus(200)
            ->assertJsonPath('stocks.0.fish_name', 'Fresh Tilapia');
    }

    public function test_seller_cannot_place_an_order(): void
    {
        // Regression test: the route only required auth:sanctum, with no
        // role check, so a seller could call POST /orders directly.
        $seller = User::factory()->seller()->create();
        $otherSeller = User::factory()->seller()->create();
        $stock = FishStock::factory()->create(['seller_id' => $otherSeller->id, 'quantity_kg' => 10]);
        $agency = DeliveryAgency::factory()->create(['seller_id' => $otherSeller->id]);

        $response = $this->actingAs($seller, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $otherSeller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
            'agency_id' => $agency->id,
        ]);

        $response->assertStatus(403);
    }

    public function test_seller_only_sees_their_own_buyers_orders_in_index(): void
    {
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10]);
        $agency = DeliveryAgency::factory()->create(['seller_id' => $seller->id]);

        $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
            'agency_id' => $agency->id,
        ])->assertStatus(201);

        $sellerOrders = $this->actingAs($seller, 'sanctum')->getJson('/api/orders');
        $sellerOrders->assertStatus(200)->assertJsonCount(1, 'data');

        $buyerOrders = $this->actingAs($buyer, 'sanctum')->getJson('/api/orders');
        $buyerOrders->assertStatus(200)->assertJsonCount(1, 'data');
    }
}
