<?php

namespace Database\Factories;

use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;

class DeliveryAgencyFactory extends Factory
{
    protected $model = \App\Models\DeliveryAgency::class;

    public function definition(): array
    {
        return [
            'seller_id' => User::factory()->seller(),
            'agency_name' => fake()->company().' Delivery',
            'contact' => fake()->phoneNumber(),
            'area_covered' => fake()->city(),
            'is_active' => true,
        ];
    }
}
