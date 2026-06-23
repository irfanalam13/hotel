"use client";

import { BedDouble, MoreHorizontal, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { useActiveOrg } from "@/components/layout/active-org";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { TableSkeleton } from "@/components/shared/table-skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { RoomFormDialog, RoomTypeFormDialog } from "@/features/rooms/room-forms";
import {
  useDeleteRoom,
  useDeleteRoomType,
  useRoomTypes,
  useRooms,
  useSetRoomStatus,
} from "@/features/rooms/hooks";
import { ROOM_STATUS, ROOM_STATUS_OPTIONS } from "@/features/rooms/status";
import { formatMoney } from "@/lib/format";

export default function RoomsPage() {
  const { activeOrg } = useActiveOrg();
  const rooms = useRooms();
  const types = useRoomTypes();
  const setStatus = useSetRoomStatus();
  const deleteRoom = useDeleteRoom();
  const deleteType = useDeleteRoomType();

  const [roomFormOpen, setRoomFormOpen] = useState(false);
  const [typeFormOpen, setTypeFormOpen] = useState(false);

  const currency = activeOrg?.currency ?? "USD";
  const roomList = rooms.data?.results ?? [];
  const typeList = types.data?.results ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Rooms"
        description="Inventory, room types and housekeeping status."
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setTypeFormOpen(true)}>
              <Plus className="size-4" /> Room type
            </Button>
            <Button onClick={() => setRoomFormOpen(true)}>
              <Plus className="size-4" /> Room
            </Button>
          </div>
        }
      />

      {/* Rooms */}
      {rooms.isLoading ? (
        <TableSkeleton cols={4} />
      ) : rooms.isError ? (
        <ErrorState description="Could not load rooms." onRetry={() => rooms.refetch()} />
      ) : roomList.length === 0 ? (
        <EmptyState
          icon={BedDouble}
          title="No rooms yet"
          description="Add a room type, then create rooms to start accepting reservations."
        />
      ) : (
        <Card className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Room</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Floor</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {roomList.map((room) => (
                <TableRow key={room.id}>
                  <TableCell className="font-medium">{room.number}</TableCell>
                  <TableCell className="text-muted-foreground">{room.room_type_name}</TableCell>
                  <TableCell className="text-muted-foreground">{room.floor || "—"}</TableCell>
                  <TableCell>
                    <Badge variant={ROOM_STATUS[room.status].variant}>
                      {ROOM_STATUS[room.status].label}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="size-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Set status</DropdownMenuLabel>
                        {ROOM_STATUS_OPTIONS.map((opt) => (
                          <DropdownMenuItem
                            key={opt.value}
                            onClick={() => setStatus.mutate({ id: room.id, status: opt.value })}
                          >
                            {opt.label}
                          </DropdownMenuItem>
                        ))}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive focus:text-destructive"
                          onClick={() => deleteRoom.mutate(room.id)}
                        >
                          <Trash2 className="size-4" /> Delete room
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

      {/* Room types */}
      <Card className="p-0">
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle className="text-base">Room types</CardTitle>
        </CardHeader>
        {types.isLoading ? (
          <div className="p-4">
            <TableSkeleton cols={3} rows={3} />
          </div>
        ) : typeList.length === 0 ? (
          <p className="px-6 pb-6 text-sm text-muted-foreground">No room types yet.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Base rate</TableHead>
                <TableHead>Capacity</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {typeList.map((t) => (
                <TableRow key={t.id}>
                  <TableCell className="font-medium">{t.name}</TableCell>
                  <TableCell>{formatMoney(t.base_rate, currency)}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {t.max_adults} adults · {t.max_children} children
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => deleteType.mutate(t.id)}
                    >
                      <Trash2 className="size-4 text-destructive" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      <RoomFormDialog open={roomFormOpen} onOpenChange={setRoomFormOpen} />
      <RoomTypeFormDialog open={typeFormOpen} onOpenChange={setTypeFormOpen} />
    </div>
  );
}
