"use client";

import { useState, useRef, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Loader2, Camera, Trash2, Eye } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Slider } from "@/components/ui/slider";
import Cropper from "react-easy-crop";
import getCroppedImg from "@/lib/cropImage";

interface ProfilePictureProps {
  fullName: string;
  initialPictureUrl?: string | null;
}

type Area = { x: number; y: number; width: number; height: number };

export function ProfilePicture({ fullName, initialPictureUrl = null }: ProfilePictureProps) {
  const [pictureUrl, setPictureUrl] = useState<string | null>(initialPictureUrl);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Crop state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState<Area | null>(null);
  const [isCropModalOpen, setIsCropModalOpen] = useState(false);
  
  // View state
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Keep internal state synced if parent changes it
  useEffect(() => {
    if (initialPictureUrl !== undefined) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPictureUrl(initialPictureUrl);
    }
  }, [initialPictureUrl]);

  const onCropComplete = (croppedArea: Area, croppedAreaPixels: Area) => {
    setCroppedAreaPixels(croppedAreaPixels);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);

    if (file.size > 5 * 1024 * 1024) {
      setError("File exceeds 5MB limit.");
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    if (!["image/jpeg", "image/png"].includes(file.type)) {
      setError("Only JPEG and PNG are allowed.");
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    setSelectedFile(file);
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      setImageSrc(reader.result?.toString() || "");
      setIsCropModalOpen(true);
      setZoom(1);
      setCrop({ x: 0, y: 0 });
    });
    reader.readAsDataURL(file);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleUploadCroppedImage = async () => {
    if (!imageSrc || !croppedAreaPixels || !selectedFile) return;

    setIsUploading(true);
    setIsCropModalOpen(false);
    
    try {
      const croppedFile = await getCroppedImg(imageSrc, croppedAreaPixels);
      
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        setError("Session expired.");
        setIsUploading(false);
        return;
      }

      const formData = new FormData();
      formData.append("file", croppedFile);

      const res = await fetch(`${API_URL}/api/v1/profile/picture`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        },
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        if (data.profile_picture_url) {
          setPictureUrl(data.profile_picture_url);
        }
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || "Failed to upload image.");
      }
    } catch (_err) {
      setError("Network error during upload.");
    } finally {
      setIsUploading(false);
      setImageSrc(null);
      setSelectedFile(null);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Are you sure you want to remove your profile photo?")) return;
    
    setError(null);
    setIsUploading(true);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const res = await fetch(`${API_URL}/api/v1/profile/picture`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${session.access_token}` }
      });

      if (res.ok || res.status === 204) {
        setPictureUrl(null);
      } else {
        setError("Failed to delete image.");
      }
    } catch (_err) {
      setError("Network error during deletion.");
    } finally {
      setIsUploading(false);
    }
  };

  const initials = fullName
    ? fullName
        .split(" ")
        .map((n) => n[0])
        .join("")
        .substring(0, 2)
        .toUpperCase()
    : "??";

  return (
    <div className="flex flex-col sm:flex-row items-center gap-6">
      <div className="relative group cursor-pointer" onClick={() => {
        if (pictureUrl) {
          setIsViewModalOpen(true);
        } else {
          fileInputRef.current?.click();
        }
      }}>
        <div className="h-24 w-24 rounded-full overflow-hidden bg-muted flex items-center justify-center border-2 border-border shadow-sm">
          {pictureUrl ? (
            <div className="relative h-full w-full">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={pictureUrl}
                alt={`${fullName}'s profile`}
                className="h-full w-full object-cover"
              />
            </div>
          ) : (
            <span className="text-2xl font-semibold text-muted-foreground uppercase">
              {initials}
            </span>
          )}
          
          {/* Overlay on hover */}
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity rounded-full">
            <Camera className="h-6 w-6 text-white" />
          </div>

          {isUploading && (
            <div className="absolute inset-0 bg-background/50 flex items-center justify-center rounded-full">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          )}
        </div>
      </div>
      
      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap gap-2">
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept="image/jpeg, image/png"
            onChange={handleFileSelect}
            aria-label="Upload profile picture"
          />
          
          {!pictureUrl ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
            >
              <Camera className="mr-2 h-4 w-4" />
              Add Photo
            </Button>
          ) : (
            <>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setIsViewModalOpen(true)}
              >
                <Eye className="mr-2 h-4 w-4" />
                View Photo
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
              >
                <Camera className="mr-2 h-4 w-4" />
                Change Photo
              </Button>
              <Button
                type="button"
                variant="destructive"
                size="sm"
                onClick={handleDelete}
                disabled={isUploading}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Remove
              </Button>
            </>
          )}
        </div>
        {error && (
          <p className="text-xs text-destructive mt-1">{error}</p>
        )}
      </div>

      {/* Crop Modal */}
      <Dialog open={isCropModalOpen} onOpenChange={setIsCropModalOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Edit Profile Photo</DialogTitle>
          </DialogHeader>
          
          {imageSrc && (
            <div className="space-y-6">
              <div className="relative h-64 w-full bg-black rounded-md overflow-hidden">
                <Cropper
                  image={imageSrc}
                  crop={crop}
                  zoom={zoom}
                  aspect={1}
                  cropShape="round"
                  showGrid={false}
                  onCropChange={setCrop}
                  onCropComplete={onCropComplete}
                  onZoomChange={setZoom}
                />
              </div>
              
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium">Zoom</span>
                <Slider
                  value={[zoom]}
                  min={1}
                  max={3}
                  step={0.1}
                  onValueChange={(val) => setZoom(Array.isArray(val) ? val[0] : (val as number))}
                  className="flex-1"
                />
              </div>
            </div>
          )}

          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setIsCropModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUploadCroppedImage} className="bg-saffron text-saffron-foreground hover:bg-saffron/90">
              Crop & Continue
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View Photo Modal */}
      <Dialog open={isViewModalOpen} onOpenChange={setIsViewModalOpen}>
        <DialogContent className="sm:max-w-md bg-black/95 border-none shadow-2xl p-0 overflow-hidden">
          {pictureUrl && (
            <div className="relative w-full aspect-square flex items-center justify-center p-8">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={pictureUrl}
                alt={`${fullName}'s profile`}
                className="max-w-full max-h-full object-contain rounded-full shadow-lg"
              />
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
