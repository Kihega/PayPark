<?php

namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use App\Models\Bill;
use App\Models\DeliveryAgency;
use App\Models\FishStock;
use App\Models\Order;
use App\Models\OrderDelivery;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class OrderController extends Controller
{
    // Buyer places an order (one or more fish items from one seller)
    public function store(Request $request)
    {
        abort_unless($request->user()->role === 'buyer', 403, 'Only buyers can place orders');

        $data = $request->validate([
            'seller_id' => 'required|exists:users,id',
            'items' => 'required|array|min:1',
            'items.*.stock_id' => 'required|exists:fish_stocks,id',
            'items.*.quantity_kg' => 'required|numeric|min:0.1',
            'payment_method' => 'required|in:mobile,bank',
            'agency_id' => 'required|exists:delivery_agencies,id',
            'delivery_method' => 'nullable|string',
        ]);

        // The agency must belong to the seller being ordered from — the
        // earlier 'exists:delivery_agencies,id' rule only checked the
        // agency exists ANYWHERE, which would let an order go through
        // with another seller's delivery partner attached.
        $agencyBelongsToSeller = DeliveryAgency::where('id', $data['agency_id'])
            ->where('seller_id', $data['seller_id'])
            ->where('is_active', true)
            ->exists();
        abort_unless($agencyBelongsToSeller, 422, 'Selected delivery agency is not available for this seller.');

        $total = 0;
        $orderItems = [];

        foreach ($data['items'] as $item) {
            $stock = FishStock::findOrFail($item['stock_id']);
            abort_unless((int) $stock->seller_id === (int) $data['seller_id'], 422, 'One of the items no longer belongs to this seller.');
            abort_if($stock->quantity_kg < $item['quantity_kg'], 422, 'Insufficient stock for '.$stock->fish_name);

            $subtotal = $stock->price_per_kg * $item['quantity_kg'];
            $total += $subtotal;

            $orderItems[] = [
                'stock_id' => $stock->id,
                'fish_name' => $stock->fish_name,
                'quantity_kg' => $item['quantity_kg'],
                'price_per_kg' => $stock->price_per_kg,
                'subtotal' => $subtotal,
            ];
        }

        $order = Order::create([
            'buyer_id' => $request->user()->id,
            'seller_id' => $data['seller_id'],
            'total_amount' => $total,
            'payment_method' => $data['payment_method'],
            'payment_status' => 'unpaid',
            'status' => 'pending',
        ]);

        foreach ($orderItems as $item) {
            $order->items()->create($item);
        }

        OrderDelivery::create([
            'order_id' => $order->id,
            'agency_id' => $data['agency_id'],
            'delivery_method' => $data['delivery_method'] ?? null,
        ]);

        return response()->json($order->load('items', 'delivery'), 201);
    }

    // Buyer marks payment done → order becomes "received", seller can now confirm
    public function pay(Request $request, Order $order)
    {
        abort_unless($order->buyer_id === $request->user()->id, 403);

        $order->update([
            'payment_status' => 'paid',
            'status' => 'received',
        ]);

        return response()->json($order);
    }

    // Seller confirms order → stock decreases, bill is generated
    public function confirm(Request $request, Order $order)
    {
        abort_unless($order->seller_id === $request->user()->id, 403);
        abort_unless($order->payment_status === 'paid', 422, 'Payment not received yet');

        $order->update(['status' => 'confirmed']);

        foreach ($order->items as $item) {
            $item->stock->decreaseStock((float) $item->quantity_kg);
        }

        Bill::firstOrCreate(
            ['order_id' => $order->id],
            [
                'buyer_id' => $order->buyer_id,
                'bill_number' => 'BILL-'.strtoupper(Str::random(8)),
                'issued_at' => now(),
            ]
        );

        return response()->json($order->load('items', 'bill'));
    }

    // List orders for the current user (buyer sees own orders, seller sees incoming orders)
    public function index(Request $request)
    {
        $user = $request->user();

        $orders = $user->role === 'seller'
            ? $user->ordersAsSeller()->with('buyer', 'items', 'delivery', 'bill')
            : $user->ordersAsBuyer()->with('seller', 'items', 'delivery', 'bill');

        return response()->json($orders->latest()->paginate(20));
    }
}
