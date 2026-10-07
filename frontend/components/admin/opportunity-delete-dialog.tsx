"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Loader2 } from "lucide-react";

interface OpportunityDeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  opportunity: Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any
  onSuccess: () => void;
}

export function OpportunityDeleteDialog({ open, onOpenChange, opportunity, onSuccess }: OpportunityDeleteDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    setIsDeleting(true);
    setError(null);
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) throw new Error("Not authenticated");

      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_URL}/api/v1/admin/opportunities/${opportunity.id}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });

      if (!res.ok) {
        throw new Error("Failed to delete opportunity");
      }

      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      setIsDeleting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Delete Opportunity?</DialogTitle>
          <DialogDescription className="pt-2">
            Are you sure you want to delete <strong>{opportunity?.title}</strong> at <strong>{opportunity?.company_name}</strong>?
            <br /><br />
            This action cannot be undone.
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="bg-destructive/15 text-destructive p-3 rounded-md text-sm mt-2">
            {error}
          </div>
        )}

        <DialogFooter className="mt-4">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isDeleting}>
            Cancel
          </Button>
          <Button type="button" variant="destructive" onClick={handleDelete} disabled={isDeleting}>
            {isDeleting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Deleting...</> : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
