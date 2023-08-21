import xml.etree.ElementTree as ET

# Check the content of the vmaf_log.json file
with open("vmaf_log.json", 'r') as file:
    vmaf_content = file.read()

vmaf_content[:500]  # Display the first 500 characters of the file content


# Parse the XML content
root = ET.fromstring(vmaf_content)

# Extract VMAF and PSNR values from frames
vmaf_values = [float(frame.get('vmaf')) for frame in root.findall('.//frame')]
psnr_values = [float(frame.get('psnr_y')) for frame in root.findall('.//frame')]

# Calculate average VMAF and PSNR
average_vmaf_xml = sum(vmaf_values) / len(vmaf_values)
average_psnr_xml = sum(psnr_values) / len(psnr_values)

average_vmaf_xml, average_psnr_xml
