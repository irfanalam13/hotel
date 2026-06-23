"use client";

import { MoreHorizontal, Pencil, Plus, Trash2, Users } from "lucide-react";
import { useState } from "react";

import { useOpenOnNew } from "@/lib/use-open-on-new";

import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { TableSkeleton } from "@/components/shared/table-skeleton";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { GuestFormDialog } from "@/features/guests/guest-form";
import { useDeleteGuest, useGuests } from "@/features/guests/hooks";
import type { Guest } from "@/types";

export default function GuestsPage() {
  const { data, isLoading, isError, refetch } = useGuests();
  const del = useDeleteGuest();

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Guest | null>(null);
  const [toDelete, setToDelete] = useState<Guest | null>(null);
  useOpenOnNew(setFormOpen);

  const guests = data?.results ?? [];

  const openCreate = () => {
    setEditing(null);
    setFormOpen(true);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Guests"
        description="Guest profiles across your properties."
        actions={
          <Button onClick={openCreate}>
            <Plus className="size-4" /> New guest
          </Button>
        }
      />

      {isLoading ? (
        <TableSkeleton cols={4} />
      ) : isError ? (
        <ErrorState description="Could not load guests." onRetry={() => refetch()} />
      ) : guests.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No guests yet"
          description="Guests are created here or automatically during reservations."
          action={
            <Button onClick={openCreate}>
              <Plus className="size-4" /> New guest
            </Button>
          }
        />
      ) : (
        <Card className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Nationality</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {guests.map((g) => (
                <TableRow key={g.id}>
                  <TableCell className="font-medium">{g.full_name}</TableCell>
                  <TableCell className="text-muted-foreground">{g.email || "—"}</TableCell>
                  <TableCell className="text-muted-foreground">{g.phone || "—"}</TableCell>
                  <TableCell className="text-muted-foreground">{g.nationality || "—"}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="size-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => { setEditing(g); setFormOpen(true); }}>
                          <Pencil className="size-4" /> Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-destructive focus:text-destructive"
                          onClick={() => setToDelete(g)}
                        >
                          <Trash2 className="size-4" /> Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      <GuestFormDialog open={formOpen} onOpenChange={setFormOpen} guest={editing} />
      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(o) => !o && setToDelete(null)}
        title={`Delete ${toDelete?.full_name}?`}
        description="This removes the guest profile."
        confirmLabel="Delete"
        destructive
        loading={del.isPending}
        onConfirm={() => {
          if (toDelete) del.mutate(toDelete.id);
          setToDelete(null);
        }}
      />
    </div>
  );
}
