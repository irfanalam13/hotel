"use client";

import { BedDouble, Building2, CalendarCheck, LogIn, Users } from "lucide-react";
import Link from "next/link";

import { useActiveOrg } from "@/components/layout/active-org";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/states";
import { StatCard } from "@/components/shared/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useMe } from "@/features/auth/hooks";
import { useGuests } from "@/features/guests/hooks";
import { useProperties } from "@/features/properties/hooks";
import { useReservations } from "@/features/reservations/hooks";
import { RESERVATION_STATUS } from "@/features/reservations/status";
import { useRooms } from "@/features/rooms/hooks";
import { formatDate, formatMoney } from "@/lib/format";

export default function DashboardPage() {
  const { activeOrg } = useActiveOrg();
  const { data: me } = useMe();
  const properties = useProperties();
  const rooms = useRooms();
  const guests = useGuests();
  const reservations = useReservations();

  const currency = activeOrg?.currency ?? "USD";
  const list = reservations.data?.results ?? [];
  const inHouse = list.filter((r) => r.status === "checked_in").length;
  const recent = list.slice(0, 6);

  const stats = [
    { label: "Properties", value: properties.data?.count ?? 0, icon: Building2, loading: properties.isLoading },
    { label: "Rooms", value: rooms.data?.count ?? 0, icon: BedDouble, loading: rooms.isLoading },
    { label: "Guests", value: guests.data?.count ?? 0, icon: Users, loading: guests.isLoading },
    { label: "In-house", value: inHouse, icon: LogIn, loading: reservations.isLoading, hint: `${reservations.data?.count ?? 0} total reservations` },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Welcome${me?.full_name ? `, ${me.full_name.split(" ")[0]}` : ""}`}
        description={activeOrg ? `${activeOrg.name} · ${activeOrg.plan} plan` : "Select an organization to begin."}
        actions={
          <Button asChild>
            <Link href="/reservations?new=1">
              <CalendarCheck className="size-4" /> New reservation
            </Link>
          </Button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s, i) => (
          <StatCard
            key={s.label}
            index={i}
            label={s.label}
            value={s.value}
            icon={s.icon}
            hint={s.hint}
            loading={s.loading}
          />
        ))}
      </div>

      <Card className="p-0">
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle className="text-base">Recent reservations</CardTitle>
          <Button asChild variant="ghost" size="sm">
            <Link href="/reservations">View all</Link>
          </Button>
        </CardHeader>
        {reservations.isLoading ? (
          <div className="p-6 text-sm text-muted-foreground">Loading…</div>
        ) : recent.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={CalendarCheck}
              title="No reservations yet"
              description="Bookings will appear here as they come in."
            />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Stay</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recent.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium">{r.code}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatDate(r.check_in)} → {formatDate(r.check_out)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={RESERVATION_STATUS[r.status].variant}>
                      {RESERVATION_STATUS[r.status].label}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatMoney(r.total_amount, r.currency || currency)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
