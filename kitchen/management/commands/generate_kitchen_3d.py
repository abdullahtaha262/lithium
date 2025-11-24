"""
Django management command to generate 3D models for kitchens using Blender.

Usage:
    python manage.py generate_kitchen_3d <kitchen_id>
    python manage.py generate_kitchen_3d --all
    python manage.py generate_kitchen_3d --check-blender
"""
from django.core.management.base import BaseCommand, CommandError
from kitchen.models import Kitchen
from kitchen.blender_utils import (
    run_blender_generation,
    check_blender_available,
    save_kitchen_json
)


class Command(BaseCommand):
    help = 'Generate 3D GLB models for kitchens using Blender'

    def add_arguments(self, parser):
        parser.add_argument(
            'kitchen_id',
            nargs='?',
            type=int,
            help='Kitchen ID to generate 3D model for'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Generate 3D models for all kitchens'
        )
        parser.add_argument(
            '--check-blender',
            action='store_true',
            help='Check if Blender is available'
        )
        parser.add_argument(
            '--blender-path',
            type=str,
            default='blender',
            help='Path to Blender executable (default: blender in PATH)'
        )
        parser.add_argument(
            '--json-only',
            action='store_true',
            help='Only generate JSON config without running Blender'
        )

    def handle(self, *args, **options):
        blender_path = options['blender_path']
        
        # Check Blender availability
        if options['check_blender']:
            self.stdout.write('Checking Blender availability...')
            available, version = check_blender_available(blender_path)
            if available:
                self.stdout.write(self.style.SUCCESS(f'✓ Blender found: {version}'))
            else:
                self.stdout.write(self.style.ERROR('✗ Blender not found'))
                self.stdout.write('Please install Blender or specify path with --blender-path')
            return
        
        # Generate for all kitchens
        if options['all']:
            kitchens = Kitchen.objects.all()
            if not kitchens.exists():
                self.stdout.write(self.style.WARNING('No kitchens found'))
                return
            
            self.stdout.write(f'Generating 3D models for {kitchens.count()} kitchen(s)...')
            success_count = 0
            
            for kitchen in kitchens:
                if self._generate_for_kitchen(kitchen, blender_path, options['json_only']):
                    success_count += 1
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully generated {success_count}/{kitchens.count()} models'
            ))
            return
        
        # Generate for specific kitchen
        kitchen_id = options.get('kitchen_id')
        if not kitchen_id:
            raise CommandError('Please provide a kitchen_id or use --all flag')
        
        try:
            kitchen = Kitchen.objects.get(pk=kitchen_id)
        except Kitchen.DoesNotExist:
            raise CommandError(f'Kitchen with ID {kitchen_id} does not exist')
        
        self._generate_for_kitchen(kitchen, blender_path, options['json_only'])

    def _generate_for_kitchen(self, kitchen, blender_path, json_only):
        """Generate 3D model for a single kitchen."""
        self.stdout.write(f'\nProcessing: {kitchen.name} (ID: {kitchen.pk})')
        self.stdout.write(f'  User: {kitchen.user.email}')
        self.stdout.write(f'  Dimensions: {kitchen.width} x {kitchen.length} x {kitchen.height}')
        self.stdout.write(f'  Objects: {kitchen.objects.count()}')
        
        if json_only:
            # Only generate JSON
            try:
                json_path = save_kitchen_json(kitchen)
                self.stdout.write(self.style.SUCCESS(f'  ✓ JSON saved: {json_path}'))
                return True
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error saving JSON: {str(e)}'))
                return False
        
        # Generate 3D model
        self.stdout.write('  Running Blender...')
        success, glb_path, error = run_blender_generation(kitchen, blender_path)
        
        if success:
            # Update kitchen model
            kitchen.model_file = glb_path
            kitchen.save(update_fields=['model_file'])
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ 3D model generated: {glb_path}'))
            return True
        else:
            self.stdout.write(self.style.ERROR(f'  ✗ Failed to generate 3D model'))
            if error:
                self.stdout.write(self.style.ERROR(f'  Error: {error}'))
            return False
