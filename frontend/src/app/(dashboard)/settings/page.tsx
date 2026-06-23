"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { useActiveOrg } from "@/components/layout/active-org";
import { PageHeader } from "@/components/shared/page-header";
import { TableSkeleton } from "@/components/shared/table-skeleton";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useCreateOrganization, useInviteMember, useMembers } from "@/features/organizations/hooks";
import {
  ROLE_OPTIONS,
  createOrgSchema,
  inviteSchema,
  type CreateOrgValues,
  type InviteValues,
} from "@/features/organizations/schema";

export default function SettingsPage() {
  const { activeOrg } = useActiveOrg();

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" description="Organization, team and workspace configuration." />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Organization</CardTitle>
          <CardDescription>Current workspace details.</CardDescription>
        </CardHeader>
        <CardContent>
          {activeOrg ? (
            <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
              <Field label="Name" value={activeOrg.name} />
              <Field label="Slug" value={activeOrg.slug} />
              <Field label="Plan" value={<Badge variant="secondary">{activeOrg.plan}</Badge>} />
              <Field label="Currency" value={activeOrg.currency} />
            </dl>
          ) : (
            <p className="text-sm text-muted-foreground">No organization selected.</p>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <MembersCard />
        <CreateOrgCard />
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-muted-foreground">{label}</dt>
      <dd className="mt-1 font-medium">{value}</dd>
    </div>
  );
}

function MembersCard() {
  const { data: members, isLoading } = useMembers();
  const invite = useInviteMember();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<InviteValues>({
    resolver: zodResolver(inviteSchema),
    defaultValues: { email: "", full_name: "", role_code: "RECEPTIONIST" },
  });

  async function onSubmit(values: InviteValues) {
    await invite.mutateAsync(values);
    reset({ email: "", full_name: "", role_code: "RECEPTIONIST" });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Team members</CardTitle>
        <CardDescription>Invite teammates and assign roles.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {isLoading ? (
          <TableSkeleton cols={2} rows={3} />
        ) : (
          <ul className="space-y-2">
            {(members ?? []).map((m) => (
              <li key={m.id} className="flex items-center gap-3">
                <Avatar name={m.user.full_name || m.user.email} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{m.user.full_name || m.user.email}</p>
                  <p className="truncate text-xs text-muted-foreground">{m.user.email}</p>
                </div>
                <Badge variant="outline">{m.role_name}</Badge>
              </li>
            ))}
            {members && members.length === 0 && (
              <li className="text-sm text-muted-foreground">No members.</li>
            )}
          </ul>
        )}

        <Separator />

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
          <div className="flex flex-col gap-2">
            <Label htmlFor="inv-email">Invite by email</Label>
            <Input id="inv-email" type="email" placeholder="teammate@hotel.com" {...register("email")} />
            {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="inv-name">Full name</Label>
              <Input id="inv-name" {...register("full_name")} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="inv-role">Role</Label>
              <Select id="inv-role" {...register("role_code")}>
                {ROLE_OPTIONS.map((r) => (
                  <option key={r.code} value={r.code}>{r.label}</option>
                ))}
              </Select>
            </div>
          </div>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Inviting…" : "Send invite"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function CreateOrgCard() {
  const create = useCreateOrganization();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateOrgValues>({
    resolver: zodResolver(createOrgSchema),
    defaultValues: { name: "", plan: "FREE" },
  });

  async function onSubmit(values: CreateOrgValues) {
    await create.mutateAsync(values);
    reset({ name: "", plan: "FREE" });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Create organization</CardTitle>
        <CardDescription>Spin up a new workspace you own.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
          <div className="flex flex-col gap-2">
            <Label htmlFor="org-name">Name</Label>
            <Input id="org-name" placeholder="Sunrise Hotels" {...register("name")} />
            {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="org-plan">Plan</Label>
            <Select id="org-plan" {...register("plan")}>
              <option value="FREE">Free</option>
              <option value="STARTER">Starter</option>
              <option value="PRO">Pro</option>
              <option value="ENTERPRISE">Enterprise</option>
            </Select>
          </div>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating…" : "Create organization"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
