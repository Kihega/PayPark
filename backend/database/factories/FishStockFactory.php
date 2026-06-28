<?php

namespace Database\Factories;

use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;

class FishStockFactory extends Factory
{
    protected $model = \App\Models\FishStock::class;

    public function definition(): array
    {
        return [
            'seller_id' => User::factory()->seller(),
            // category_id is nullable (the "Select category" field was
            // removed from the add-stock form) — omitted here on purpose,
            // matching how stocks are actually created in the app now.
            'fish_name' => fake()->randomElement(['Tilapia', 'Nile Perch', 'Sardine', 'Catfish']),
            'quantity_kg' => fake()->randomFloat(2, 1, 100),
            'price_per_kg' => fake()->randomFloat(2, 1000, 20000),
            'status' => 'active',
        ];
    }
}
