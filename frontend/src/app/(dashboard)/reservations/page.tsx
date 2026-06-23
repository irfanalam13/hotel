"use client";

import { CalendarCheck, LogIn, LogOut, MoreHorizontal, Plus, XCircle } from "lucide-react";
import { useState } from "react";

import { useOpenOnNew } from "@/lib/use-open-on-new";

import { useActiveOrg } from "@/components/layout/active-org";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { TableSkeleton } from "@/components/shared/table-skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ReservationFormDialog } from "@/features/reservations/reservation-form";
import { useReservationAction, useReservations } from "@/features/reservations/hooks";
import { RESERVATION_STATUS } from "@/features/reservations/status";
import { formatDate, formatMoney } from "@/lib/format";
import type { Reservation } from "@/types";

export default function ReservationsPage() {
  const { activeOrg } = useActiveOrg();
  const { data, isLoading, isError, refetch } = useReservations();
  const action = useReservationAction();

  const [formOpen, setFormOpen] = useState(false);
  const [toCancel, setToCancel] = useState<Reservation | null>(null);
  useOpenOnNew(setFormOpen);

  const currency = activeOrg?.currency ?? "USD";
  const reservations = data?.results ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reservations"
        description="Bookings, check-ins and check-outs."
        actions={
          <Button onClick={() => setFormOpen(true)}>
            <Plus className="size-4" /> New reservation
          </Button>
        }
      />

      {isLoading ? (
        <TableSkeleton cols={6} />
      ) : isError ? (
        <ErrorState description="Could not load reservations." onRetry={() => refetch()} />
      ) : reservations.length === 0 ? (
        <EmptyState
          icon={CalendarCheck}
          title="No reservations yet"
          description="Create a booking to see it here. Availability is checked in real time."
          action={
            <Button onClick={() => setFormOpen(true)}>
              <Plus className="size-4" /> New reservation
            </Button>
          }
        />
      ) : (
        <Card className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Stay</TableHead>
                <TableHead>Rooms</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Total</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {reservations.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium">{r.code}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatDate(r.check_in)} → {formatDate(r.check_out)}
                    <span className="ml-1 text-xs">({r.nights}n)</span>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {r.rooms.map((rm) => rm.room_number ?? rm.room_type_name).join(", ") || "—"}
                  </TableCell>
                  <TableCell>
                    <Badge variant={RESERVATION_STATUS[r.status].variant}>
                      {RESERVATION_STATUS[r.status].label}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatMoney(r.total_amount, r.currency || currency)}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="size-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {r.status === "booked" && (
                          <DropdownMenuItem
                            onClick={() => action.mutate({ id: r.id, action: "checkIn" })}
                          >
                            <LogIn className="size-4" /> Check in
                          </DropdownMenuItem>
                        )}
                        {r.status === "checked_in" && (
                          <DropdownMenuItem
                            onClick={() => action.mutate({ id: r.id, action: "checkOut" })}
                          >
                            <LogOut className="size-4" /> Check out
                          </DropdownMenuItem>
                        )}
                        {(r.status === "booked" || r.status === "inquiry") && (
                          <DropdownMenuItem
                            className="text-destructive focus:text-destructive"
                            onClick={() => setToCancel(r)}
                          >
                            <XCircle className="size-4" /> Cancel
                          </DropdownMenuItem>
                        )}
                        {!["booked", "checked_in", "inquiry"].includes(r.status) && (
                          <DropdownMenuItem disabled>No actions</DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      <ReservationFormDialog open={formOpen} onOpenChange={setFormOpen} />
      <ConfirmDialog
        open={!!toCancel}
        onOpenChange={(o) => !o && setToCancel(null)}
        title={`Cancel ${toCancel?.code}?`}
        description="This frees the assigned rooms and marks the reservation cancelled."
        confirmLabel="Cancel reservation"
        destructive
        loading={action.isPending}
        onConfirm={() => {
          if (toCancel) action.mutate({ id: toCancel.id, action: "cancel" });
          setToCancel(null);
        }}
      />
    </div>
  );
}
