"use client";

import { motion } from "framer-motion";
import { Hotel } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LoginForm } from "@/features/auth/login-form";

export default function LoginPage() {
  return (
    <main className="grid min-h-screen lg:grid-cols-2">
      {/* Brand panel */}
      <div className="relative hidden flex-col justify-between overflow-hidden bg-primary p-12 text-primary-foreground lg:flex">
        <div className="flex items-center gap-2">
          <div className="flex size-9 items-center justify-center rounded-lg bg-primary-foreground/10">
            <Hotel className="size-5" />
          </div>
          <span className="text-lg font-semibold">HMS</span>
        </div>
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-3xl font-semibold leading-tight">
            Run every property from one calm, fast workspace.
          </h2>
          <p className="mt-3 max-w-md text-primary-foreground/70">
            Reservations, rooms, guests and teams — multi-tenant by design.
          </p>
        </motion.div>
        <span className="text-sm text-primary-foreground/50">© Hotel Management System</span>
      </div>

      {/* Form panel */}
      <div className="flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="w-full max-w-sm"
        >
          <Card>
            <CardHeader>
              <CardTitle className="text-2xl">Sign in</CardTitle>
              <CardDescription>Enter your credentials to access your workspace.</CardDescription>
            </CardHeader>
            <CardContent>
              <LoginForm />
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </main>
  );
}
