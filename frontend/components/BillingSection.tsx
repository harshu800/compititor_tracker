"use client";

import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useApi } from "@/hooks/useApi";
import { ApiError } from "@/lib/api";
import { SITE_NAME } from "@/lib/seo";

declare global {
  interface Window {
    Razorpay: new (options: RazorpayOptions) => { open: () => void };
  }
}

interface RazorpayOptions {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description: string;
  order_id: string;
  handler: (response: {
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
  }) => void;
  modal?: { ondismiss?: () => void };
  theme?: { color: string };
}

interface CreateOrderResponse {
  order_id: string;
  amount: number;
  currency: string;
  key_id: string;
}

interface PlanInfo {
  plan: string;
  pro_plan_amount: number;
  pro_plan_currency: string;
}

function loadRazorpayScript(): Promise<boolean> {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

function formatAmount(amountInSmallestUnit: number, currency: string): string {
  const major = amountInSmallestUnit / 100;
  const symbol = currency === "INR" ? "₹" : currency === "USD" ? "$" : `${currency} `;
  return `${symbol}${major.toLocaleString()}`;
}

export function BillingSection() {
  const { call, organizationId } = useApi();
  const queryClient = useQueryClient();
  const [checkingOut, setCheckingOut] = useState(false);
  const [downgrading, setDowngrading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const { data: planInfo, isLoading } = useQuery({
    queryKey: ["billing-plan", organizationId],
    queryFn: () => call<PlanInfo>("/api/v1/billing/plan"),
    enabled: !!organizationId,
  });

  useEffect(() => {
    loadRazorpayScript();
  }, []);

  async function handleUpgrade() {
    setError(null);
    setSuccess(null);
    setCheckingOut(true);
    try {
      const scriptReady = await loadRazorpayScript();
      if (!scriptReady) {
        throw new Error("Couldn't load the payment form. Check your connection and try again.");
      }

      const order = await call<CreateOrderResponse>("/api/v1/billing/create-order", {
        method: "POST",
        body: { plan: "pro" },
      });

      const razorpay = new window.Razorpay({
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: SITE_NAME,
        description: "Upgrade to Pro",
        order_id: order.order_id,
        theme: { color: "#111827" },
        modal: {
          ondismiss: () => setCheckingOut(false),
        },
        handler: async (response) => {
          try {
            await call("/api/v1/billing/verify", {
              method: "POST",
              body: {
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              },
            });
            setSuccess("You're upgraded to Pro. Thanks!");
            queryClient.invalidateQueries({ queryKey: ["billing-plan", organizationId] });
          } catch (e) {
            setError(
              e instanceof ApiError
                ? e.message
                : "Payment succeeded but we couldn't confirm the upgrade — contact support with your payment id."
            );
          } finally {
            setCheckingOut(false);
          }
        },
      });
      razorpay.open();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : e instanceof Error ? e.message : "Something went wrong.");
      setCheckingOut(false);
    }
  }

  async function handleDowngrade() {
    setError(null);
    setSuccess(null);
    setDowngrading(true);
    try {
      await call("/api/v1/billing/downgrade", { method: "POST" });
      setSuccess("You're back on the Free plan.");
      queryClient.invalidateQueries({ queryKey: ["billing-plan", organizationId] });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't switch to Free — try again in a moment.");
    } finally {
      setDowngrading(false);
    }
  }

  const plan = planInfo?.plan ?? "free";

  return (
    <section className="bg-white rounded-xl border border-gray-200 p-5 max-w-lg">
      <h2 className="text-sm font-semibold text-gray-900 mb-1">Billing</h2>
      <p className="text-xs text-gray-500 mb-4">Manage your workspace&apos;s plan.</p>

      {isLoading ? (
        <p className="text-sm text-gray-400">Loading…</p>
      ) : (
        <>
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-sm text-gray-500">Current plan</div>
              <div className="font-medium text-gray-900 capitalize">{plan}</div>
            </div>
            {plan === "free" && (
              <button
                onClick={handleUpgrade}
                disabled={checkingOut}
                className="bg-gray-900 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
              >
                {checkingOut ? "Opening checkout…" : "Upgrade to Pro"}
              </button>
            )}
            {plan !== "free" && (
              <button
                onClick={handleDowngrade}
                disabled={downgrading}
                className="border border-gray-300 text-gray-700 rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50 hover:bg-gray-50"
              >
                {downgrading ? "Switching…" : "Downgrade to Free"}
              </button>
            )}
          </div>

          {plan === "free" && planInfo && (
            <p className="text-xs text-gray-400">
              Pro unlocks 50 competitors, 500 pages, email alerts, and CSV export — {" "}
              {formatAmount(planInfo.pro_plan_amount, planInfo.pro_plan_currency)}/month via Razorpay.
            </p>
          )}
          {plan !== "free" && (
            <p className="text-xs text-gray-400">
              Downgrading takes effect immediately and won&apos;t remove any competitors or history you&apos;ve
              already added — you&apos;ll just be limited to the Free plan&apos;s 5 competitors / 20 pages going forward.
            </p>
          )}

          {success && (
            <p className="text-sm text-green-700 bg-green-50 border border-green-100 rounded-lg px-3 py-2 mt-3">
              {success}
            </p>
          )}
          {error && (
            <p className="text-sm text-red-700 bg-red-50 border border-red-100 rounded-lg px-3 py-2 mt-3">
              {error}
            </p>
          )}
        </>
      )}
    </section>
  );
}
