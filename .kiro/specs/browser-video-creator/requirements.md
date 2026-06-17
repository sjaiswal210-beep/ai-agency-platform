# Requirements Document

## Introduction

A browser-based video creation tool integrated into the business owner dashboard at `/api/panel/{website_id}`. Business owners can upload photos from their device, add text overlays, and auto-generate a promotional video with transitions and free background music. All processing happens entirely client-side using WebAssembly (FFmpeg.wasm) or a React-based video framework (Remotion), ensuring zero server storage. Once the video is downloaded, all in-memory assets are cleared.

## Glossary

- **Video_Creator**: The client-side video creation module rendered within the owner dashboard panel
- **Photo_Uploader**: The component responsible for accepting and validating image files from the user's device
- **Text_Overlay_Editor**: The component that allows users to add, position, and style text overlays on photos
- **Video_Renderer**: The client-side engine (FFmpeg.wasm or Remotion) that composes photos, transitions, text overlays, and audio into a video file
- **Transition_Engine**: The sub-component that applies visual transition effects between photo slides
- **Music_Library**: A bundled set of royalty-free background music tracks available for video creation
- **Owner_Dashboard**: The existing server-rendered HTML page at `/api/panel/{website_id}` serving as the business management interface
- **Asset_Manager**: The in-browser memory management component responsible for holding and releasing media assets

## Requirements

### Requirement 1: Photo Upload

**User Story:** As a business owner, I want to upload photos from my device, so that I can use them as slides in my promotional video.

#### Acceptance Criteria

1. WHEN the business owner selects photos from their device, THE Photo_Uploader SHALL accept image files in JPEG, PNG, and WebP formats
2. WHEN the business owner selects photos, THE Photo_Uploader SHALL allow selection of between 2 and 20 photos in a single session
3. WHEN a selected file exceeds 10 MB in size, THE Photo_Uploader SHALL reject the file and display a size limit error message
4. WHEN a selected file is not a valid image format, THE Photo_Uploader SHALL reject the file and display a format error message
5. WHEN photos are uploaded, THE Photo_Uploader SHALL display thumbnail previews of all selected images
6. WHEN photos are uploaded, THE Photo_Uploader SHALL store all image data exclusively in browser memory without sending data to any server
7. WHEN the business owner reorders photos via drag-and-drop, THE Photo_Uploader SHALL update the slide sequence to match the new order

### Requirement 2: Text Overlay

**User Story:** As a business owner, I want to add text overlays on my photos, so that I can include my business name, offers, or messages in the video.

#### Acceptance Criteria

1. WHEN the business owner activates text editing on a slide, THE Text_Overlay_Editor SHALL provide a text input field for entering overlay content
2. WHEN the business owner enters text, THE Text_Overlay_Editor SHALL render the text visually on the photo preview in real time
3. THE Text_Overlay_Editor SHALL provide font size options of small, medium, and large
4. THE Text_Overlay_Editor SHALL provide font color selection with at least 8 preset colors and a custom hex input
5. WHEN the business owner positions the text overlay, THE Text_Overlay_Editor SHALL allow placement at top, center, or bottom of the slide
6. WHEN the business owner adds text to a slide, THE Text_Overlay_Editor SHALL limit text to 100 characters per overlay
7. THE Text_Overlay_Editor SHALL allow up to 2 text overlays per slide

### Requirement 3: Video Generation

**User Story:** As a business owner, I want to auto-generate a video from my uploaded photos, so that I can create professional-looking promotional content easily.

#### Acceptance Criteria

1. WHEN the business owner triggers video generation, THE Video_Renderer SHALL compose all uploaded photos into a sequential video with each photo displayed for 3 seconds
2. WHEN composing the video, THE Transition_Engine SHALL apply a visual transition effect between consecutive photos lasting 0.5 seconds
3. THE Transition_Engine SHALL provide at least 3 transition styles: fade, slide, and zoom
4. WHEN the business owner selects a transition style, THE Video_Renderer SHALL apply the selected transition uniformly across all slide transitions
5. WHEN generating the video, THE Video_Renderer SHALL process all frames entirely within the browser using WebAssembly or a React-based rendering pipeline
6. WHEN video generation begins, THE Video_Renderer SHALL display a progress indicator showing percentage of completion
7. WHEN video generation is complete, THE Video_Renderer SHALL produce an MP4 file with H.264 encoding at 720p resolution (1280x720)
8. IF video generation fails due to insufficient browser memory, THEN THE Video_Renderer SHALL display an error message suggesting the user reduce the number of photos

### Requirement 4: Background Music

**User Story:** As a business owner, I want background music automatically added to my video, so that the video feels professional and engaging without manual audio editing.

#### Acceptance Criteria

1. THE Music_Library SHALL include at least 5 royalty-free background music tracks
2. WHEN video generation starts, THE Video_Renderer SHALL automatically attach a background music track to the generated video
3. THE Music_Library SHALL provide a preview playback control for each available track before generation
4. WHEN the business owner selects a music track, THE Video_Renderer SHALL use the selected track as background audio
5. WHEN no track is explicitly selected, THE Video_Renderer SHALL use the first track in the library as the default
6. WHEN the video duration exceeds the music track duration, THE Video_Renderer SHALL loop the music track to match the video length
7. WHEN the video duration is shorter than the music track duration, THE Video_Renderer SHALL trim the music to match the video length with a 1-second fade-out

### Requirement 5: Video Download and Cleanup

**User Story:** As a business owner, I want to download the generated video and have all temporary data cleared, so that no storage is consumed on the server.

#### Acceptance Criteria

1. WHEN video generation is complete, THE Video_Creator SHALL present a download button to the business owner
2. WHEN the business owner clicks the download button, THE Video_Creator SHALL trigger a browser file download of the generated MP4 file
3. WHEN the download completes or the business owner navigates away from the Video_Creator, THE Asset_Manager SHALL release all in-memory photo data, audio data, and video data from browser memory
4. THE Asset_Manager SHALL revoke all created object URLs after download or navigation away
5. THE Video_Creator SHALL confirm to the business owner that no data has been stored on the server at any point during the process
6. IF the business owner closes the browser tab during video generation, THEN THE Asset_Manager SHALL release all allocated memory through standard browser garbage collection

### Requirement 6: Dashboard Integration

**User Story:** As a business owner, I want to access the video creator from my existing dashboard, so that I can find and use the tool alongside my other business management features.

#### Acceptance Criteria

1. THE Owner_Dashboard SHALL display a Video Creator tool card in the Manage Your Business tools grid section
2. WHEN the business owner clicks the Video Creator tool card, THE Owner_Dashboard SHALL navigate to the Video_Creator page
3. THE Video_Creator page SHALL be accessible at the route `/api/panel/{website_id}/video-creator`
4. THE Video_Creator page SHALL load all required JavaScript libraries (FFmpeg.wasm or Remotion bundle) from a CDN or static asset path without requiring server-side rendering for the video logic
5. WHILE the Video_Creator page is loading dependencies, THE Video_Creator SHALL display a loading indicator with a message indicating library initialization

### Requirement 7: User Experience and Responsiveness

**User Story:** As a business owner using a mobile device, I want the video creator interface to work smoothly on my phone, so that I can create videos on the go.

#### Acceptance Criteria

1. THE Video_Creator SHALL render a responsive layout optimized for viewports between 320px and 500px width
2. THE Video_Creator SHALL maintain usability on touch devices with tap targets of at least 44x44 pixels
3. WHEN the business owner completes all steps, THE Video_Creator SHALL present a clear sequential workflow: upload photos, add text, choose music, generate video, download
4. WHILE video generation is in progress, THE Video_Creator SHALL disable the generate button to prevent duplicate generation requests
5. THE Video_Creator SHALL display all interface text in English with simple, non-technical language suitable for non-technical business owners
